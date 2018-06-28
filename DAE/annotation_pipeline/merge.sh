head -n 1 $1-part-01-0 >> $1
for f in $1-part-*-*; do
  echo $f
  tail -n +2 $f >> $1
done
rm -rf $1-part-*-*