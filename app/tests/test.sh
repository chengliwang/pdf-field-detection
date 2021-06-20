export PYTHONPATH=/app

echo -e "\n| --------------------- Running unit tests ------------------------- |"
coverage run -m pytest -s
coverage report --omit="venv/*,tests/*,*/.pyenv*" -i
