import os
import subprocess
import csv

# Settings
start_dir = 5
end_dir = 405
master_peak_file = "master.tab"
output_csv = "intensities_series.csv"

def extract_intensities():
    peaks = []
    # 1. Read the master peak list to identify peaks and assignments
    with open(master_peak_file, 'r') as f:
        lines = f.readlines()
        vars_line = [l for l in lines if l.startswith("VARS")][0]
        header_parts = vars_line.split()
        
        # NMRPipe VARS start at index 1 because index 0 is 'VARS'
        id_idx = header_parts.index("INDEX") - 1
        ass_idx = header_parts.index("ASS") - 1
        height_idx = header_parts.index("HEIGHT") - 1
        
        for line in lines:
            if line.startswith("VARS") or line.startswith("FORMAT") or not line.strip() or "NULL" in line:
                continue
            parts = line.split()
            if len(parts) < max(id_idx, ass_idx): continue
            peaks.append({"id": parts[id_idx], "name": parts[ass_idx]})

    # Dictionary to store data: { 'PeakID': ['ResidueName', 'Int5', 'Int6', ...] }
    results = {p['id']: [p['name']] for p in peaks}
    
    # 2. Setup the CSV Header: INDEX, ASS, 5, 6, 7...
    csv_header = ["INDEX", "ASS"] + [str(i) for i in range(start_dir, end_dir + 1)]

    # 3. Loop through directories to get intensities
    for i in range(start_dir, end_dir + 1):
        spec_path = f"./{i}/hsqc.ft2"
        out_tab = f"./{i}/fitted.tab"
        
        if not os.path.exists(spec_path):
            print(f"Directory {i}: hsqc.ft2 not found. Filling with 0.")
            for p_id in results:
                results[p_id].append("0.0")
            continue
        
        print(f"Processing directory {i}...")

        # Use getTab to extract height from the spectrum at master coordinates
        cmd = f"getTab -in {master_peak_file} -spec {spec_path} -out {out_tab}"
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if os.path.exists(out_tab):
            with open(out_tab, 'r') as f:
                tab_lines = f.readlines()
                for line in tab_lines:
                    if not line.strip() or any(x in line for x in ["VARS", "FORMAT", "NULL"]):
                        continue
                    parts = line.split()
                    try:
                        p_id = parts[id_idx]
                        height = parts[height_idx]
                        if p_id in results:
                            results[p_id].append(height)
                    except IndexError:
                        continue
        else:
            for p_id in results:
                results[p_id].append("0.0")

    # 4. Write to CSV with proper numeric sorting for the INDEX
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(csv_header)
        
        # Sort keys numerically (handling potential decimals like 356.0)
        sorted_keys = sorted(results.keys(), key=lambda x: int(float(x)))
        for p_id in sorted_keys:
            # Clean the ID to be a clean integer for the CSV
            clean_id = int(float(p_id))
            writer.writerow([clean_id] + results[p_id])

    print(f"\nDone! CSV saved as: {output_csv}")

if __name__ == "__main__":
    extract_intensities()
