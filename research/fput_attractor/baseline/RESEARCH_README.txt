Nonlinear Waves Research — consolidated Stage 1 and Stage 2 package (14 October 2026)

- See Nonlinear_Waves_Stage2/STAGE2_FINDINGS.md for results, limitations and rerun instructions.
- See Nonlinear_Waves_Stage2/NEXT_HANDOFF.md for separate Codex/Claude Code and Work briefs.
- Starting point: Stage 1 implementation from the preceding research turn.

Install Python 3.10+ and packages with:
pip install -r Nonlinear_Waves_Stage2/requirements.txt

Then from this root, run:
python -m unittest discover -s Nonlinear_Waves_Stage2 -p test_stage2.py -v
python Nonlinear_Waves_Stage2/toda_benchmark.py

No API calls or authentication are needed.
