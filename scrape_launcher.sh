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
   --no-vnc)
      no_vnc=true
      str_param+="--no-vnc $no_vnc "
      printf "%s " " --no-vnc='$no_vnc';"
      ;;
   --rebuild)
      rebuild=true
      str_param+="--rebuild $rebuild "
      printf "%s " " rebuild='$rebuild';"
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

printf "\npython app/app.py > \n"
python app/app.py
printf "< python app/app.py\n\n"

echo "Changing directory to: $start_dir"
cd "$start_dir" || err_exit $?
echo "pwd: $(pwd)"

deactivate