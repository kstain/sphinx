import os
import sys
import glob
import imp
import cjson
import types
import hashlib
import traceback 

import re
import argparse

import copy
from pprint import pprint

import base
import multi
import chash

# CONN stuffs
#

CONN = None
def fetch_conn():
    global CONN
    # TODO, can need change to be an input
    # but if I put it out of function, "cfg" is not defined
    db_map = chash.config().DB_MULTI_MAP

    if CONN is None:
        print 'making DB connection:'
        dbmulitmap = copy.deepcopy(db_map)
        for v in dbmulitmap.values():
            if 'passwd' in v['info']:
                v['info']['passwd'] = '****'
        pprint(dbmulitmap)
        CONN = multi.MultiConnection(db_map=db_map)
    return CONN

def get_conn_id(cursor):
    cursor.execute('select CONNECTION_ID()')
    if not cursor.rowcount:
        return -1
    
    conn_id = cursor.fetchone()
    if conn_id is None:
        return -1
    return conn_id[0]

# REVISION TABLE stuffs
#

REVISION_CREATE = '''
CREATE  TABLE IF NOT EXISTS `%(rev_table_name)s` (
  `rev_num` INT(11) UNSIGNED NOT NULL,
  `table_name` VARCHAR(128) NOT NULL,
  `created` BIGINT(20) UNSIGNED NOT NULL COMMENT 'UTC Timestamp in Milliseconds' ,
  `info` TEXT NULL,
  PRIMARY KEY (`rev_num`, `table_name`))
ENGINE = InnoDB
'''

def make_revision_tables(revision_table, mconn=None):
    conn = mconn if mconn else fetch_conn()
    for part_id in chash.db_all(conn):
        cursor = conn.real_cursor(part_id)
        cnt = cursor.execute('show tables like "%s"' % revision_table)
        if cnt == 0:
            cursor.execute(REVISION_CREATE % {
                'rev_table_name': revision_table})
            print 'MADE %s in part %d' % (revision_table, part_id)

DB_REVISIONS = None
def query_revision_table(revision_table):
    global DB_REVISIONS
    # queries the entire revision table into memory, by partition
    #
    conn = fetch_conn()
    rev_rows = {}
    for part_id in chash.db_all(conn):
        rev_rows.setdefault(part_id, {})
        cursor = conn.real_cursor(part_id)
        cursor.execute('select rev_num, table_name, created from %s' % (
            revision_table,))
        for row in cursor.fetchall():
            revnum = row[0]
            table_name = row[1]
            rev_rows[part_id].setdefault(revnum, []).append(table_name)
    DB_REVISIONS = rev_rows

def save_table_revision(cursor, revision_table, rev_num, table_name):
    sql = '''
    insert into %s (rev_num, table_name, created)
    values (%s, "%s", UNIX_TIMESTAMP())
    ''' % (revision_table, rev_num, table_name)
    cursor.execute(sql)
    cursor.execute('commit')


AUTO_R = re.compile(r"AUTO_INCREMENT=\d*")
def _get_create_table(cursor, tablename):
    cursor.execute('show create table `%s`' % tablename)
    if not cursor.rowcount:
        return None
    s = cursor.fetchone()[-1]
    # we want to strip out AUTOINCREMENT pieces
    #
    m = AUTO_R.findall(s)
    try:
        if m:
            s = s.replace(m[0], '')
    except:
        traceback.print_exc()
        print 'FINDALL:', m
        print s
    return s



def query_create_tables():
    conn = fetch_conn()
    data = {}
    for part_id in chash.db_all(conn):
        cursor = conn.real_cursor(part_id)
        cursor.execute('show tables')
        tables = [x[0] for x in cursor.fetchall()]
        for tname in tables:
            create_t = _get_create_table(cursor, tname)
            data.setdefault(tname, {})[part_id] = create_t
    return data

# REVISIONs
#
class Revision(object):

    def __init__(self, revnum, rev_tablename, path, tables):
        self._path    = path
        self._revnum  = revnum 
        self._revtable_name = rev_tablename
        self._srcs    = []       
        self._tmodule = tables

    def __repr__(self):
        return 'Revision %d <%s> [%d]' % (self._revnum, self._path, len(self._srcs))

    def read(self):
        self._read_table_module()
        self._read_sources()

    def _read_table_module(self):
        if os.path.exists(os.path.join(self._path, "tables.py")):
            self._tmodule = imp.load_source(
                "tables_r%04d" % self._revnum,  
                os.path.join(self._path, "tables.py"))

    def _read_sources(self):
        sql_names = glob.glob('%s/*.sql' % self._path)
        for fname in sql_names:
            raw_sql = file(fname).read()
            shortname = os.path.split(fname)[-1]
            table_name = shortname.replace('.sql', '')
            table_klass = getattr(self._tmodule, table_name, None)
            in_table_klass = getattr(self._tmodule, '%sInternal' % table_name, None)
            if table_klass is None:
                print 'Unknown Table:', table_name, 'in revision', self._revnum
                continue
            self._srcs.append(
                RevisionSource(
                    self._revnum,
                    self._revtable_name,
                    table_name, 
                    table_klass, 
                    in_table_klass,
                    raw_sql))
            self._srcs[-1].parse()

    def apply(self):
        for src in self._srcs:
            src.apply()

META_TAG = '-- META:'
class RevisionSource(object):

    def __init__(self, revnum, rev_table_name, tname, tklass, in_tklass, raw_sql):
        self._revnum  = revnum
        self._revtable_name = rev_table_name
        self._tname   = tname
        self._tklass  = tklass
        self._in_tklass  = in_tklass
        self._raw_sql = raw_sql
        
        self._stmts = []
        self._metas = []

        conn = fetch_conn()
        parts = chash.db_list(conn, self._tklass.group)
        self._parts = {}
        for p in parts:
            self._parts[p] = {'applied': None,}

    def __repr__(self):
        return 'RSource %s <%d> [%d]' % (
            self._tname, len(self._stmts), len(self._metas))

    def parse(self):
        self.parse_stmts()
        self.parse_meta()
        self.check_db()

    def parse_stmts(self):
        raw_stmts = _strip_meta(self._raw_sql)
        self._stmts = filter(lambda l: bool(l.strip()), raw_stmts.split(';'))

    def parse_meta(self):
        lines = self._raw_sql.split('\n')
        self._metas = []
        for ln in lines:
            if not ln.startswith(META_TAG):
                continue
            cmdinfo = self._parse_extra(ln)
            self._metas.append(cmdinfo)

    def _parse_extra(self, ln):
        ln = ln.replace(META_TAG, '').strip()
        cmdinfo = {}
        if ln == 'insert_marker':
            cmdinfo['cmd'] = 'insert_marker'
        elif ln.startswith('insert_row_n'):
            parsed = ln.split('|')
            cmd = parsed[0].strip()
            row = cjson.decode(parsed[1])
            cmdinfo = {'cmd' : cmd, 
                       'row' : row, 
                       'n'   : int(parsed[2])}        
        elif ln.startswith('insert_row'):
            parsed = ln.split('|')
            cmd = parsed[0].strip()
            row = cjson.decode(parsed[1])
            cmdinfo = {'cmd' : cmd, 'row' : row}        
        return cmdinfo

    def check_db(self):
        if not DB_REVISIONS:
            print 'DB_REVISIONS not set, unable to decern if revision applied.'
            return None

        create_tables = {}
        for part_id in self._parts.keys():
            check = DB_REVISIONS.get(part_id, {}).get(self._revnum, {})
            self._parts[part_id]['applied'] = self._tname in check 

    def apply(self):
        conn = fetch_conn()
        for part_id, info in self._parts.items():
            print 'applying REV %s TABLE %s PART %s... ' % (
                    self._revnum, self._tname, part_id), 
            if info.get('applied') == True:
                print 'already applied'
                continue
            cursor = conn.real_cursor(part_id)
            s_cnt = self.apply_stmts(cursor)
            m_cnt = self.apply_metas(part_id, cursor)

            print 'GREAT SUCCESS [with %d extras]' % m_cnt
            save_table_revision(cursor, self._revtable_name, self._revnum, self._tname)

    def apply_stmts(self, cursor):
        cnt = 0
        for stmt in self._stmts:
            cnt += cursor.execute(stmt)
        return cnt
        
    def apply_metas(self, part_id, cursor):
        cnt = 0
        tklass = self._tklass
        if tklass.extern:
            tklass = self._in_tklass
        for meta in self._metas:
            cmd = meta['cmd']
            if cmd == 'insert_marker':
                mrk_sql = _marker_sql(part_id, tklass)
                cnt += cursor.execute(mrk_sql)
            elif cmd == 'insert_row_n':
                row = meta['row']
                n = meta['n']
                for i in xrange(n):
                    row_sql = _insert_sql(tklass, row)
                    cnt += cursor.execute(row_sql)
            elif cmd == 'insert_row':
                row = meta['row']
                row_sql = _insert_sql(tklass, row)
                cnt += cursor.execute(row_sql)
        return cnt

    def applied(self):
        applied = [None]
        rows = self._parts.items()
        rows.sort()
        applied = []
        for part_id, info in rows:
            if info['applied'] is None:
                applied.append('.')
            elif info['applied']:
                applied.append('T')
            else:
                applied.append('F')
        return applied

def read_rev_sources(where, rev_tablename, tables):
    revs = {}
    for n in os.listdir(where):
        try:
            revnum = int(n)
        except ValueError, e:
            continue
        revpath = os.path.join(where, n)
        R = revs.setdefault(revnum, Revision(revnum, rev_tablename, revpath, tables))
        R.read()
    return revs 

def rev_summary(rev):
    print 'REV %s' % rev._revnum
    for src in rev._srcs:
        print '%40s %s' % (src._tname, ''.join(src.applied()))

def filter_revs(data, revs):
    l = data.keys()
    l.sort()
    last_revnum = l[-1]

    if revs is None:
        # return the last revision only
        #
        return {last_revnum : data[last_revnum]}

    if ':' not in revs:
        revnum = int(revs)
        return {revnum : data[revnum]}

    s, e = revs.split(':')
    start = int(s) if s else 1
    end   = int(e) if e else last_revnum
    d = {}
    for revnum in xrange(start, end+1):
        d[revnum] = data[revnum]
    return d


# UTILS
#

def _marker_sql(part_id, tklass):
    return 'ALTER TABLE %s AUTO_INCREMENT=%ld' % (tklass.table_name, chash.db_push(part_id)+1)

def _insert_sql(tklass, row):
    flattened = row.items()
    keys   = [x[0] for x in flattened]
    values = [x[1] for x in flattened]
    for i, val in enumerate(values):
        if isinstance(val, types.StringType):
            values[i] = '"%s"' % val
        else:
            values[i] = '%s' % val

    sql = 'INSERT INTO `%s` (%%(cols)s) VALUES (%%(vals)s); ' % tklass.table_name
    args = {
        'cols': ','.join(keys), 
        'vals': ','.join(values),
        }
    return sql % args


def _prompt(msg=''):
    v = raw_input(msg)
    v = v.strip().lower()
    if v in ('y', 'yes'):
        return True
    return False

META_RE  = re.compile('^--(.)*$', re.M)
def _strip_meta(raw_sql):
    while True:
        raw_sql, n = META_RE.subn('', raw_sql)
        if n == 0:
            break
    return raw_sql

def _ch(s):
    return hashlib.md5(s).hexdigest()

def checksum_create_tables(unsplit_tables, checker = _ch):
    global DB_CREATE_TABLES
    DB_CREATE_TABLES = query_create_tables()
    bad = []
    table_count = 0
    for tname, info in DB_CREATE_TABLES.items():
        if tname in unsplit_tables:
            continue
        # if there's only one bit of info, this means a non-split table, which
        # we don't want to worry about
        #
        if len(info) == 1:
            continue
        table_count += 1
        keys = info.keys()
        base_create_t = info[keys.pop()]
        for key in keys:
            if checker(base_create_t) != checker(info[key]):
                bad.append(tname)

    if bad:
        print 'CHECKSUM FAILS on %d tables!' % len(bad)
        bad.sort()
        for b in bad:
            print '   %s' % b
    else:
        print 'CHECKSUM PASSES! %d tables checked.' % table_count
    return bad

def arg_parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '-v', '--verbose', 
        default=False, 
        action='store_true',
        help='Verbose status output.',
    )
    parser.add_argument(
        '--yes', 
        default=None, 
        action='store_true', 
        help = 'Answer yes to all prompts (and apply changes).')
    parser.add_argument(
        '-R', '--revs', 
        default = None,
        help='By default the comands work off of the latest revision directory '
            ' in the db/schema dir. This forces things to work of this revision.'
            ' Can be formated like python slice, so 1 is just that revision, 1: ' 
            ' is all revision from 1 until the end, etc.')
    parser.add_argument(
        '-S', '--checksum', 
        default = False, 
        action = 'store_true', 
        help = 'Just preform the create_table checksums and exist.',
        )
    return parser


