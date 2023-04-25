#!/usr/bin/zsh


err_exit(){
  echo '[ERROR]'
  printf "%s " "Press enter to continue"
  read -r
  exit "$1"
}

# Get the option
r_key=false

printf "%s " "Params: "
while [ "$#" -gt 0 ]
do
   case "$1" in
   -f|--freeze)
      r_key=true
      printf "%s " " freeze;"
      ;;
   -*)
      echo "Invalid option '$1'. Use -h|--help to see the valid options" >&2
      return 1
      ;;
   *)
      echo "Invalid option '$1'. Use -h|--help to see the valid options" >&2
      return 1
   ;;
   esac
   shift
done
echo

echo "start_dir: $(pwd)"
start_dir=$(pwd)

echo "base_dir: $(dirname "$0")"
base_dir=$(dirname "$0")
if [ "$base_dir" != "." ]; then
  echo "Changing directory to: $base_dir"
  cd "$base_dir" || err_exit $?
  echo "pwd: $(pwd)"
fi

echo "Venv activating:"
source ./venv/bin/activate || err_exit $?
echo "Venv activated successful"

if [ "$r_key" = true ]; then
    echo "pip freeze:"
    pip freeze
fi

printf "\npython getting_data/scrape_app.py > \n"
python getting_data/scrape_app.py
printf "< python getting_data/scrape_app.py\n\n"

echo "Changing directory to: $start_dir"
cd "$start_dir" || err_exit $?
echo "pwd: $(pwd)"

deactivate