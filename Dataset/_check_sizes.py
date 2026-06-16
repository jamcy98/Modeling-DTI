import pandas as pd, json

with open(r"C:\Users\Jamila\Modeling-DTI\Dataset\raw\kiba\ligands_can.txt") as f:
    kiba = json.load(f)
print(f"KIBA:      {len(kiba):>8,} unique drugs")

bdb = pd.read_csv(r"C:\Users\Jamila\Modeling-DTI\Dataset\raw\bindingdb\BindingDB_DTI.csv", usecols=["smiles"])
print(f"BindingDB: {bdb['smiles'].nunique():>8,} unique drugs")

chem = pd.read_csv(r"C:\Users\Jamila\Modeling-DTI\Dataset\raw\chembl\chembl_DTI.csv", usecols=["smiles"])
print(f"ChEMBL:    {chem['smiles'].nunique():>8,} unique drugs")
