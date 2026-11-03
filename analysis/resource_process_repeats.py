import bootstrap, subprocess, sys
import pandas as pd
from run_benchmark import R, O

for rep in range(5):
    subprocess.run(
        [sys.executable, str(R / "robustness.py"), "--resource-rep", str(rep)],
        check=True,
    )
pd.concat([pd.read_csv(O / f"resource_repeat_{rep}.csv") for rep in range(5)]).to_csv(
    O / "resource_repeats.csv", index=False
)
print("Five sequential process repetitions complete")
