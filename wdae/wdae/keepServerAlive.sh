while true; do
    echo ping...
    for n in `seq 20`; do
        wget -O - http://wigserv2.cshl.edu/dae/api/effect_types > /dev/null 2> /dev/null
    done
    sleep 60 
done
