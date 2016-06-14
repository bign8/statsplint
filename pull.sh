scp -r gitcode@hgsilo.ddns.net:/home/gitcode/datashare/data/ __data
rm -r __data/players
mv __data/data/* __data/.
rm -r __data/data
