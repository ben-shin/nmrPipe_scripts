import os
import subprocess
import csv

start_dir = 5
end_dir = 405
master_peak_file = "master.tab"
output_csv = "intensities_series.csv"

def extract_intensities():
    peaks = []
    with open(master_peak_file, 'r') as f:
        lines = f.readlines()
        header = lines[0].split()
        ass_idx = header.index("ASS")
        id_idx = header.index("INDEX")
        
        for line in lines:
            if line.startswith("VARS") or line.startswith("FORMAT") or not line.strip() or "NULL" in line:
                continue
            parts = line.split()
            peaks.append({"id": parts[id_idx], "name": parts[ass_idx]})

    results = {p['id']: [p['name']] for p in peaks}
    headers = ["Peak_ID", "Residue"]

    for i in range(start_dir, end_dir + 1):
        spec_path = f"./{i}/hsqc.ft2"
        out_tab = f"./{i}/fitted.tab"
        
        if not os.path.exists(spec_path):
            print(f"Skipping {i}: {spec_path} not found.")
            continue
        
        print(f"Processing directory {i}...")
        headers.append(f"Int_{i}")

        cmd = f"getTab -in {master_peak_file} -spec {spec_path} -out {out_tab}"
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
      
        if os.path.exists(out_tab):
            with open(out_tab, 'r') as f:
                tab_lines = f.readlines()
                for line in tab_lines:
                    if line.startswith("VARS") or line.startswith("FORMAT") or not line.strip() or "NULL" in line:
                        continue
                    parts = line.split()
                    p_id = parts[0]
                    height = parts[17] 
                    if p_id in results:
                        results[p_id].append(height)
        else:
            for p_id in results:
                results[p_id].append("0.0")

    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for p_id in sorted(results.keys(), key=int):
            writer.writerow([p_id] + results[p_id])

    print(f"Saved intensities to {output_csv}")

if __name__ == "__main__":
    extract_intensities()
