#!/bin/sh

version=1.0
destdir=ancient_earth-${version}

mkdir -p release
cd release

mkdir -p ${destdir}/datta
cd ${destdir}

rsync -avP \
	  --exclude '*.xcf' --exclude '*.pyc' --exclude '*.tmx' --exclude release --exclude .git --exclude '*~' \
	  ../../ datta/
mv datta/README.md .

cat > run.sh <<EOF
#!/bin/sh
cd \$(dirname \$0)/datta
python main.py
EOF
chmod +x run.sh
