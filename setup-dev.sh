dir=$(dirname $0)
virtualenv $dir/venv

source $dir/venv/bin/activate
pip install -r $dir/requirements/dev.txt
deactivate
