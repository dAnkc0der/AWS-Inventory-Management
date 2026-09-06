# AWS Resource Inventory & Audit Tool

A Python CLI tool that scans an AWS account across five core services — EC2, EBS, S3, RDS, and Security Groups — and produces a structured inventory with basic security and cost-risk findings, exported to both JSON and CSV.

Built with `boto3` as a hands-on project to learn AWS API scripting, structured error handling, and Python module design.


## Prerequisites

- Python 3.8+
- AWS credentials configured locally (`aws configure`) with at least read-only permissions for EC2, S3, RDS, and CloudWatch
- `boto3` installed:
  ```bash
  pip install boto3
  ```

## Usage

Run with defaults (region: `us-east-1`, output prefix: `inventory`):

```bash
python inventory.py
```

Specify a region and custom output filename prefix:

```bash
python inventory.py --region us-west-2 --output my_audit
```

### Output

Running the tool generates one JSON and one CSV file per resource type:

```
<output>_ec2.json / .csv
<output>_ebs.json / .csv
<output>_s3.json  / .csv
<output>_rds.json / .csv
<output>_sg.json  / .csv
```
