#!/bin/sh

mnt_rak.sh

export PYTHONPATH=/usr/local/lib64/python2.7/site-packages:$PYTHONPATH
cd $HOME/src/psfm

if [ -z "`ps axuw | grep [x]mms2d`" ]; then
	xmms2d -q &
	sleep 1
fi

./psfm.py
