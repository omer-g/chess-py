# The ValueError exceptions can be printed with no need to do something
class NotOnBoardException(ValueError):
    pass

class SameSquareException(ValueError):
    pass

class NoPieceException(ValueError):
    pass

class WrongTurnException(ValueError):
    pass

class SameColorException(ValueError):
    pass

class IllegalMoveException(ValueError):
    pass

class KingThreatenedException(ValueError):
    pass

class PromotionWaitException(ValueError):
    pass

class RevertException(ValueError):
    pass

# A missing king means program should terminate
class NoKingError(RuntimeError):
    pass
