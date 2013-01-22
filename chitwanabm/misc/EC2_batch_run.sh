#!/bin/bash

EC2_MANAGER="ubuntu@ec2-54-242-233-203.compute-1.amazonaws.com"
BASE_PATH="/home/azvoleff/ChitwanABM"
REMOTE_BASE_PATH="/home/ubuntu/ChitwanABM"
MODEL_PATH="/home/azvoleff/ChitwanABM"

ssh $EC2_MANAGER true || { echo "ERROR logging into run manager" >&2; exit; }

for rcfile in $(find $BASE_PATH/rcfiles -maxdepth 1 -mindepth 1 -type f) ; do
    echo "Processing $rcfile"
    /home/azvoleff/Code/Python/chitwanabm/chitwanabm/threaded_batch_run.py --rc $rcfile
done

CURTIME=$(date +%Y%m%d-%H%M%S)
TARFILENAME="$BASE_PATH/Tarballs/ChitwanABM_Runs-$HOSTNAME-$CURTIME.tar.gz"
echo $TARFILENAME
tar -czvf $TARFILENAME $BASE_PATH/Runs
scp $TARFILENAME $EC2_MANAGER:$REMOTE_BASE_PATH/Tarballs

#shutdown -h now
