
#Import standard Python Libraries
import re
import pandas as pd
from datetime import datetime
import argparse
import sys


def parse_fix_line(line: str):
    """Converts FIX line to a dictionary
    
    Args:
        line: str
        
    Returns:
        Dictionary mapping
        
    Raises:
        IndexError: If input line isn't able to be split
    """

    try:
        msg = line.split(":", 1)[1]
    except IndexError:
        return {}
    
    # support either real SOH (\x01) or caret-A ^A in files
    msg = msg.replace("^A", "\x01")
    parts = msg.strip().split('\x01')
    fix_dict = {}
    for p in parts:
        if "=" in p:
            tag, val = p.split("=", 1)
            fix_dict[tag] = val
    return fix_dict


def main():
    
    #argparse used to assist in parsing arguments
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument('--input_fix_file', required=True)
    parser.add_argument('--output_csv_file', required=True)
    args = parser.parse_args()

    #Parameters
    input_fix_file = args.input_fix_file
    output_csv_file = args.output_csv_file

    with open(input_fix_file, "r") as f:
        lines = f.readlines()
    orders = {}
    fills = []
    for line in lines:
        fix = parse_fix_line(line)

        msg_type = fix.get("35")

        #Checks for New Order Single(D) and Limit Order (2)
        if msg_type == 'D' and fix['40'] == '2':
            client_order_id = fix['11']
            if client_order_id:
                orders[client_order_id] = {
                    'OrderID': client_order_id,
                    'OrderTransactTime': fix['60'],
                    'Symbol': fix['55'],
                    'Side': fix['54'],
                    'OrderQty': fix['38'],
                    'LimitPrice': fix['44'],
                }

        #Checks for MsgType (35) = Execution Report (8)
        elif msg_type == '8':
            # Check for Fully Filled limit orders, ignore partially filled limit orders
            if fix['150'] == '2' and fix['39'] == '2' and fix['40'] == '2':
                client_order_id = fix['11']
                if client_order_id in orders:
                    order = orders[client_order_id]
                    fills.append({
                        'OrderID': client_order_id,
                        'OrderTransactTime': order['OrderTransactTime'],
                        'ExecutionTransactTime': fix['60'],
                        'Symbol': order['Symbol'],
                        'Side': order['Side'],
                        'OrderQty': order['OrderQty'],
                        'LimitPrice': order['LimitPrice'],
                        'AvgPx': fix['6'],
                        'LastMkt': fix['30'],
                    })

    #Create dataframe of filled orders
    filled_orders = pd.DataFrame(fills)
    print("Parsed rows:", len(filled_orders))

    #Save to CSV file
    filled_orders.to_csv(output_csv_file, index=False)
    print(f"CSV saved to {output_csv_file}")


if __name__ == '__main__':
    try:
        main()
    except KeyError as e:
        # Helpful hard-stop if a required tag is missing (better than silently wrong output)
        print(f"Missing expected FIX tag: {e}. Recheck that fields are inputed correctly.", file=sys.stderr)
        sys.exit(1)
