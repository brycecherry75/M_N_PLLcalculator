import argparse, sys, math

if __name__ == "__main__":
  parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
  parser.add_argument("--dacclk", type=float, required='yes', help="Desired DAC frequency in Hz")
  parser.add_argument("--refmin", type=float, required='yes', help="Reference frequency minimum in Hz")
  parser.add_argument("--refmax", type=float, required='yes', help="Reference frequency maximum in Hz")
  parser.add_argument("--refclk", type=float, required='yes', help="Reference frequency in Hz")
  parser.add_argument("--refdiv", type=int, default=1, help="Reference divider (default: 1)")
  parser.add_argument("--nmin", type=int, default=3, help="N divider minimum (default: 3)")
  parser.add_argument("--nmax", type=int, default=1023, help="N divider maximum (default: 1023)")
  parser.add_argument("--phaseminfreq", type=float, required='yes', help="Phase comparator minimum frequency in Hz")
  parser.add_argument("--phasemaxfreq", type=float, required='yes', help="Phase comparator maximum frequency in Hz")
  parser.add_argument("--mmin", type=int, default=3, help="M divider minimum (default: 3)")
  parser.add_argument("--mmax", type=int, default=1023, help="M divider maximum (default: 1023)")
  parser.add_argument("--vcominfreq", type=int, required='yes', help="VCO minimum frequency in Hz")
  parser.add_argument("--vcomaxfreq", type=int, required='yes', help="VCO maximum frequency in Hz")
  parser.add_argument("--vcoloopdiv", type=int, required='yes', help="VCO loop divider")
  parser.add_argument("--postdividerratios", type=int, required='yes', help="Post divider power of 2 ratio count")

  args = parser.parse_args()

  if args.dacclk <= 0:
    print("ERROR: Desiered DAC frequency is zero or negative")
    sys.exit(0)
  if args.refclk <= 0:
    print("ERROR: Reference clock frequency is zero or negative")
    sys.exit(0)
  if args.refmin <= 0:
    print("ERROR: Reference clock frequency mimimum is zero or negative")
    sys.exit(0)
  if args.refmax <= 0:
    print("ERROR: Reference clock frequency maximum is zero or negative")
    sys.exit(0)
  if args.refmin > args.refmax:
    print("ERROR: Reference clock frequency maximum is smaller than its minimum")
    sys.exit(0)
  if args.refclk > args.refmax or args.refclk < args.refmin:
    print("ERROR: Reference clock frequency is out or range")
    sys.exit(0)
  if args.refdiv <= 0:
    print("ERROR: Reference divider is zero or negative")
    sys.exit(0)
  if args.nmin <= 0:
    print("ERROR: N divider minimum is zero or negative")
    sys.exit(0)
  if args.nmax <= 0:
    print("ERROR: N divider maximum is zero or negative")
    sys.exit(0)
  if args.nmin > args.nmax:
    print("ERROR: N divider maximum is smaller than its minimum")
    sys.exit(0)
  if args.phaseminfreq <= 0:
    print("ERROR: Phase comparator minimum output frequency is zero or negative")
    sys.exit(0)
  if args.phasemaxfreq <= 0:
    print("ERROR: Phase comparator minimum output frequency is zero or negative")
    sys.exit(0)
  if args.phaseminfreq > args.phasemaxfreq:
    print("ERROR: Phase comparator maximum output frequency is smaller than its minimum")
    sys.exit(0)
  if args.mmin <= 0:
    print("ERROR: M divider minimum is zero or negative")
    sys.exit(0)
  if args.mmax <= 0:
    print("ERROR: M divider maximum is zero or negative")
    sys.exit(0)
  if args.mmin > args.mmax:
    print("ERROR: M divider maximum is smaller than its minimum")
    sys.exit(0)
  if args.vcominfreq <= 0:
    print("ERROR: VCO frequency minimum is zero or negative")
    sys.exit(0)
  if args.vcomaxfreq <= 0:
    print("ERROR: VCO frequency maximum is zero or negative")
    sys.exit(0)
  if args.vcominfreq > args.vcomaxfreq:
    print("ERROR: VCO frequency maximum is smaller than its minimum")
    sys.exit(0)
  if args.vcoloopdiv <= 0:
    print("ERROR: VCO loop divider is zero or negative")
    sys.exit(0)
  if args.postdividerratios <= 0:
    print("ERROR: Post divider power of 2 ratio count is zero or negative")
    sys.exit(0)

  PostDivider = 0
  for DividerToTry in range (args.postdividerratios):
    temp = (1 << DividerToTry)
    vco = (args.dacclk * temp)
    if vco >= args.vcominfreq and vco <= args.vcomaxfreq: # for 25.175 MHz DAC and VCO limits of 48-220 MHz, result is 2
      PostDivider = temp
      break
  if PostDivider == 0:
    print("ERROR: Output frequency is not within limits of", str((args.vcominfreq / (1 << (args.postdividerratios - 1)))) + "-" + str(args.vcomaxfreq), "Hz")
    sys.exit(0)

  RequiredMNratio = (args.dacclk * (10**6) * PostDivider) / (args.refclk / args.refdiv) # multiply desired DAC clock by 10**6 for fidelity - for 14.31818 MHz reference/25.175 MHz DAC/reference divider = 1/post divider = 2: (25175000 * 10**6 * 2) / (14318180 / 1) = 3516508.3830486835617375951412819
  BestN = -1
  BestM = -1
  FrequencyError = args.vcomaxfreq
  NegativeFrequencyError = False
  MinimumN = int(math.ceil(args.refclk / args.refdiv / args.phasemaxfreq)) # for 2 MHz: ceil(14318180 / 1 / 2000000) = 8
  MaximumN = int(math.floor(args.refclk / args.refdiv / args.phaseminfreq)) # for 150 kHz: floor(14318180 / 1 / 150000) = 95
  for NtoMatch in range (args.nmax):
    if NtoMatch < MinimumN or NtoMatch < args.nmin:
      continue
    elif NtoMatch > MaximumN:
      break
    else:
      M = int(((NtoMatch * RequiredMNratio) / (10**6) / args.vcoloopdiv) + 0.5) # round it; if N = 91, M will be 80 rounded
      if M >= args.mmin and M <= args.mmax:
        CurrentFrequencyError = (args.dacclk - (((args.refclk / args.refdiv) * (M * args.vcoloopdiv)) / NtoMatch / PostDivider)) # (25175000 - (((14318180 / 1) * (80 * 4)) / 91 / 2)) = -178.02197802066803 Hz error
        if CurrentFrequencyError < 0:
          NegativeFrequencyError = True
          CurrentFrequencyError *= -1
        else:
          NegativeFrequencyError = False
        if CurrentFrequencyError < FrequencyError:
          FrequencyError = CurrentFrequencyError
          BestM = M
          BestN = NtoMatch
          if FrequencyError == 0:
            break

  if BestN == -1 or BestM == -1:
    print("ERROR: Unable to calculate suitable M/N values within phase comparator frequency limits")
    sys.exit(0)

  if NegativeFrequencyError == True:
    FrequencyError *= -1
  print("M/N values are", str(BestM) + "/" + str(BestN), "with frequency error of", FrequencyError, "Hz and post divider ratio of", PostDivider)