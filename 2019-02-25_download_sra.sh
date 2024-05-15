cd ~/quilt_data/20240115_ccle_metadata_schemas/fastq/2019-02-25/
for SRA in $(cat 2019-02-25_sra.txt):
do
    echo $SRA
    prefetch -v $SRA
    fastq-dump --split-3 $SRA
    rm -rf $SRA
done;
