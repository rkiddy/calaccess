

if [ "$1" != "" ] && [ "$2" = "" ]; then
    echo ""
    echo "Please give 2 dates to see differences, or none to see last two dates."
    echo ""
    exit
fi

if [ "$1" = "" ]; then
    echo "select distinct(last_mod) from files order by last_mod desc limit 2;" | \
        mysql --skip-column-names ca_calaccess > /tmp/last_$$_1

else
    echo "$1 $2" > /tmp/last_$$_1
fi

cat /tmp/last_$$_1 | \
    tr '\n' ' ' | sed 's/ $//' | \
    awk '{print "select filename, last_mod, num_lines from files where ";
          print "   last_mod in ('\''"$1"'\'', '\''"$2"'\'')";
          print "   and filename like '\''%TSV'\'';"}' | \
    mysql --skip-column-names ca_calaccess | \
    awk 'BEGIN{FS="/"}{print $NF}' | \
    sort | \
    awk 'BEGIN{last=""}{if ($1 != last) print ""; print $0; last=$1; count=$3}' | \
    awk '{if ($0 == "") count=-1;
          print $0;
          if (($0 != "") && (count > 1)) print "after: "$3", before: "count", diff: "($3-count);
          if ($0 != "") count=$3}'

echo ""



