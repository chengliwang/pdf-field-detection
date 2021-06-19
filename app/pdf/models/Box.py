class Box:
    def __init__(self, position):
        self.Position = position
        self.FieldPosition = None
        self.IsHorizontal = False
        self.LeftPadding = 0
        self.RightPadding = 0
        self.LineWidth = 0
        self.TopElement = None
        self.Prefix = None
        self.PrefixGap = 0
        self.Suffix = None
        self.SuffixGap = 0
        self.HasCentLine = False
        self.HasComboLine = False
        self.FieldCode = None
        self.IsMarkupField = False