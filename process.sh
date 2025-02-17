#!/bin/bash

# Logs
logfile='log/process.log'
error_logfile='log/process-error.log'

# Set timestamp format
date_string=$(date +"%Y-%m-%d %H:%M:%S")
script=$(basename "$0")
timestamp=$$

# Logging functions
set -E
function error_formatter {
  printf "[%s] ERROR: %s {\"script\": \"%s\", \"message\": \"%s\", \"pid\": \"%s\"} \n" \
    "$date_string" "$1" "$script" "$2" "$timestamp" | tee -a "$error_logfile"
}
trap error_formatter ERR

function log_formatter {
  printf "[%s] INFO: %s {\"script\": \"%s\", \"pid\": \"%s\"} \n" \
    "$date_string" "$1" "$script" "$timestamp" | tee -a "$logfile"
}

# HELP function
function usage {
  cat <<EOF

Create a PDF or EPUB page.

Usage:
  --format [pdf|epub]  -> Specify output format
  --json [relative path]  -> Specify the source file
  --pb [0|1]           -> Paperbook (PDF only)
  --bw [0|1]           -> Black and white (PDF only)
  --s  [0|1]           -> Short version (PDF only)
  --l  [0|1]           -> Language (PDF only)
  --et [kindle|epub|web] -> EPUB type (EPUB only)

EOF
}

# Kill process if something goes wrong
function die {
  error_formatter "die" "${1}"
  exit 1
}

# Parse arguments
while [ $# -gt 0 ]; do
  case $1 in
    --help)
      usage
      exit 0
      ;;
    --*)
      v="${1/--/}"
      declare "$v"="$2"
      shift
      ;;
  esac
  shift
done

# Check required parameters
if [[ -z $format ]]; then
  usage
  die "Missing required parameter: --format"
fi

if [[ $format == "pdf" ]]; then
  [[ -z $json || -z $pb || -z $bw || -z $s || -z $l ]] && usage && die "PDF requires --json --pb, --bw, --s, --l"
  command="python3 /src/consumer.py --format pdf --json \"$json\" --pb \"$pb\" --bw \"$bw\" --s \"$s\" --l \"$l\""
elif [[ $format == "epub" ]]; then
  [[ -z $json || -z $et ]] && usage && die "EPUB requires --json --et"
  command="python3 /src/consumer.py --format epub --json \"$json\" --et \"$et\""
else
  usage
  die "Invalid format: $format"
fi

# Execute the command
log_formatter "Executing command: $command"
docker exec book-with-python /bin/sh -c "$command"
