class TextLine:
    def __init__(self, text, position):
        self.Text = text.strip().encode("ascii", "replace").decode()
        self.Position = position