#!/usr/bin/env python3
# Required Libraries: pip install boto3 pyathena pandas
# https://laughingman7743.github.io/PyAthena/usage.html#basic-usage

import boto3
from pyathena import connect
from pyathena.pandas.util import as_pandas

# Configuration
s3_bucket = "quilt-example-bucket"
s3_prefix = "ccle/"
athena_database = "userathenadatabase-2htmlbiqyvry"
athena_table = "ccle_pyathena"
output_location = f"s3://{s3_bucket}/athena_results/"
region_name = "us-east-1"

# Initialize the Athena and S3 clients
s3_client = boto3.client("s3", region_name=region_name)
athena_client = boto3.client("athena", region_name=region_name)

# Step 1: List sample folders in the S3 bucket
response = s3_client.list_objects_v2(Bucket=s3_bucket, Prefix=s3_prefix, Delimiter="/")
sample_folders = [folder["Prefix"].split("/")[-2] for folder in response.get("CommonPrefixes", [])]

# Step 2: Create the Athena table if it doesn't exist
create_table_query = f"""
CREATE EXTERNAL TABLE IF NOT EXISTS {athena_database}.{athena_table} (
    column1 data_type,
    column2 data_type,
    ...
)
PARTITIONED BY (sample_name string)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
STORED AS INPUTFORMAT 'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION 's3://{s3_bucket}/{s3_prefix}';
"""

athena_client.start_query_execution(
    QueryString=create_table_query,
    QueryExecutionContext={"Database": athena_database},
    ResultConfiguration={"OutputLocation": output_location},
)

# Step 3: Add partitions for each sample
for sample in sample_folders:
    add_partition_query = f"""
    ALTER TABLE {athena_database}.{athena_table}
    ADD PARTITION (sample_name='{sample}')
    LOCATION 's3://{s3_bucket}/{s3_prefix}{sample}/';
    """
    athena_client.start_query_execution(
        QueryString=add_partition_query,
        QueryExecutionContext={"Database": athena_database},
        ResultConfiguration={"OutputLocation": output_location},
    )

# Step 4: Perform a cross-sectional analysis query
query = f"""
SELECT sample_name, AVG(column1) as avg_col1, SUM(column2) as sum_col2
FROM {athena_database}.{athena_table}
GROUP BY sample_name;
"""

# Execute the query and fetch the results
cursor = connect(s3_staging_dir=output_location, region_name=region_name).cursor()
cursor.execute(query)
df = as_pandas(cursor)

# Step 5: Display or process the results
print(df)
