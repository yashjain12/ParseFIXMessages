#Import standard Python Libraries
import pandas as pd
from datetime import datetime
import argparse
import sys

def main():

    #argparse used to assist in parsing arguments
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('--input_csv_file', required=True)
    parser.add_argument('--output_metrics_file', required=True)
    args = parser.parse_args()

    #Parameters
    input_csv_file = args.input_csv_file
    output_metrics_file = args.output_metrics_file

    try:
        order_file = pd.read_csv(input_csv_file)
    except FileNotFoundError:
        print(f"Input file {input_csv_file} not found.")
        sys.exit(1)

    #Convert time columns to datetime for calculations
    order_file['OrderTransactTime'] = pd.to_datetime(order_file['OrderTransactTime'], errors='coerce')
    order_file['ExecutionTransactTime'] = pd.to_datetime(order_file['ExecutionTransactTime'], errors='coerce')

    #Calculate execution speed in seconds, which is the time from order transaction to execution
    order_file['ExecSpeedSecs'] = (order_file['ExecutionTransactTime'] - order_file['OrderTransactTime']).dt.total_seconds()

    #Calculate price improvement
    order_file['LimitPrice'] = pd.to_numeric(order_file['LimitPrice'], errors='coerce')
    order_file['AvgPx'] = pd.to_numeric(order_file['AvgPx'], errors='coerce')
    order_file['PriceImprovement'] = abs(order_file['LimitPrice'] - order_file['AvgPx'])

    #Calculate average metrics 
    average_metrics = order_file.groupby('LastMkt', dropna=False).agg(
        AvgPriceImprovement=('PriceImprovement', 'mean'),
        AvgExecSpeedSecs=('ExecSpeedSecs', 'mean')
    ).reset_index()

    #Save metrics to CSV
    average_metrics.to_csv(output_metrics_file, index=False)
    print(f"CSV saved to {output_metrics_file}")


if __name__ == '__main__':
    main()
