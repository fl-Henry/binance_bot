#!/usr/bin/zsh


err_exit(){
  echo '[ERROR]'
  printf "%s " "Press enter to continue"
  read -r
  exit "$1"
}

# Get the option
r_key=false

str_param=""
printf "%s " "Params: "
while [ "$#" -gt 0 ]
do
   case "$1" in
   -f|--freeze)
      r_key=true
      printf "%s " " freeze;"
      ;;
   --first-symbol)
      shift
      first_symbol="$1"
      str_param+="--first-symbol $first_symbol "
      printf "%s " " first symbol='$first_symbol';"
      ;;
   --second-symbol)
      shift
      second_symbol="$1"
      str_param+="--second-symbol $second_symbol "
      printf "%s " " second-symbol='$second_symbol';"
      ;;
   --id)
      shift
      id="$1"
      str_param+="--id $id "
      printf "%s " " id=$id;"
      ;;
     --test)
      test="--test"
      str_param+="$test "
      printf "%s " "$test;"
      ;;
     --force-url)
      force_url="--force-url"
      str_param+="$force_url "
      printf "%s " " $force_url';"
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

echo "$str_param"
echo "python ./bot_logic.py:"
while true ; do echo "$str_param" | xargs python ./bot_logic.py || sleep 5; done
echo
echo "python: closed"

echo "Changing directory to: $start_dir"
cd "$start_dir" || err_exit $?
echo "pwd: $(pwd)"

deactivate