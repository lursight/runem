from runem.informative_dict import InformativeDict, ReadOnlyInformativeDict

OptionName = str
OptionValue = bool
OptionsWritable = InformativeDict[OptionName, OptionValue]
OptionsReadOnly = ReadOnlyInformativeDict[OptionName, OptionValue]
Options = OptionsReadOnly
