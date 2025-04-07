
import pygame
from sys import exit

pygame.init()

WIDTH = 800
HEIGHT = 800
MAP_SIZE = 10
CELL_SIZE = 64
PIECE_SIZE = 48

class Piece():
    def __init__(self, color, pos):
        self.pos = pos
        self.color = color
        self.isKing = False
        self.isDead = False
        self.isJumping = False
        self.isMovable = False
        self.isAvailable = False

    def Kill(self, map_, pos) -> bool:
        if abs(pos[0] - self.pos[0]) < 1:
            return False
        dir_ = ((pos[0] - self.pos[0]) / abs(pos[0] - self.pos[0]),(pos[1] - self.pos[1]) / abs(pos[0] - self.pos[0]))
        newPos = self.pos
        killed = False
        while newPos != pos:
            newPos = (newPos[0] + dir_[0], newPos[1] + dir_[1])
            cell = map_.GetCell(newPos)
            if cell.color != self.color and cell.color != "blank":
                cell.isDead = True
                killed = True
        return killed

    def Move(self, map_, pos, players):
        killed = self.Kill(map_, pos)
        map_.SetCell(self.pos, Blank())
        map_.SetCell(pos, self)
        self.pos = pos
        if killed:
            self.isJumping = True
            if not self.Find(map_, self.pos):
                self.isJumping = False
                map_.Refresh(players)
                if (self.pos[0] == 0 and self.color == "white") or (self.pos[0] == map_.size - 1 and self.color == "black"):
                    self.isKing = True
        else:
            map_.Refresh(players)
            if (self.pos[0] == 0 and self.color == "white") or (self.pos[0] == map_.size - 1 and self.color == "black"):
                self.isKing = True

    def Find(self, map_, pos, redir_=(0,0), nedir_=0) -> list:
        available = []
        movable = []
        self.isAvailable = False
        for i in [-1,1]:
            for j in [-1,1]:
                if (-i,-j) == redir_ or i * j == nedir_:
                    continue
                movable_, cell = self.__FindNext(map_, pos, (i,j))
                if cell:
                    if cell.color != self.color and not cell.isDead:
                        newPos, cell = self.__FindNext(map_, cell.pos, (i,j))
                        if newPos:
                            self.isAvailable = True
                            for pos_ in newPos:
                                available.append(pos_)
                if not self.isJumping:
                    if not self.isKing:
                        if self.color == "white" and i == 1:
                            continue
                        elif self.color == "black" and i == -1:
                            continue
                    if movable_:
                        for pos_ in movable_:
                            movable.append(pos_)
        if available != []:
            return available
        return movable

    def __FindNext(self, map_, pos, dir_):
        tryLimit = 1
        movable = []
        if self.isKing:
            tryLimit = map_.size
        while tryLimit > 0:
            pos = (pos[0] + dir_[0], pos[1] + dir_[1])
            cell = map_.GetCell(pos)
            if not cell:
                break
            if cell.color != "blank":
                break
            movable.append(pos)
            tryLimit -= 1
        return movable, cell

class Blank():
    def __init__(self):
        self.color = "blank"
        self.isDead = True

class Map():
    def __init__(self, WIDTH, HEIGHT, size, Pos2Num):
        self.pos = (WIDTH / 2, HEIGHT / 2)
        self.size = size
        self.__map = {}
        self.turn = "white"
        self.__MapInitializer(Pos2Num)
        self.Pos2Num = Pos2Num
        self.winner = None

    def __MapInitializer(self, Pos2Num):
        for row in range(self.size):
            for col in range(self.size):
                if ( row + col ) % 2 == 1:
                    if row < 4:
                        self.__map[Pos2Num((row,col))] = Piece("black", (row,col))
                    elif row > 5:
                        self.__map[Pos2Num((row,col))] = Piece("white", (row,col))
                    else:
                        self.__map[Pos2Num((row,col))] = Blank()

    def GetCell(self, pos):
        if isinstance(pos, int):
            return self.__map.get(pos, None)
        return self.__map.get(self.Pos2Num(pos), None)

    def SetCell(self, pos, item):
        self.__map[self.Pos2Num(pos)] = item

    def JudgeWin(self, players):
        player = players[self.turn]
        if len(player.pieces) == 0:
            self.winner = "white" if player.color == "black" else "black"

    def Refresh(self, players):
        self.turn = "white" if self.turn == "black" else "black"
        players[self.turn].pieces = {}
        for row in range(self.size):
            for col in range(self.size):
                if ( row + col ) % 2 == 1:
                    cell = self.__map[self.Pos2Num((row,col))]
                    if cell and cell.color != "blank":
                        if cell.isDead:
                            self.__map[self.Pos2Num((row,col))] = Blank()
                        elif cell.color == self.turn:
                            players[self.turn].pieces[self.Pos2Num((row,col))] = cell
        players[self.turn].MovementCacheUpdate(self)
        self.JudgeWin(players)

class Player():
    def __init__(self, map_, color):
        self.color = color
        self.pieces = {}
        self.InitPieces(map_)
        self.movementCache = {}
        self.virtualPiece = None
        self.haveAvailable = False

    def InitPieces(self, map_):
        for num in range(1, int(map_.size ** 2 / 2 + 1)):
            cell = map_.GetCell(num)
            if cell.color == self.color:
                self.pieces[num] = cell

    def ApplyMovement(self, piece, map_):
        piece.Move(map_, piece.pos, self)

    def MovementCacheUpdate(self, map_):
        self.haveAvailable = False
        self.movementCache = {}
        for piece in self.pieces.values():
            if not piece:
                continue
            piece.isMovable = False
            self.movementCache[piece] = piece.Find(map_, piece.pos)
            if self.movementCache[piece]:
                piece.isMovable = True
            if piece.isAvailable:
                print(piece.pos)
                self.haveAvailable = True

class Game():
    def __init__(self):
        self.WIDTH = WIDTH
        self.HEIGHT = HEIGHT
        self.screen = pygame.display.set_mode((self.WIDTH,self.HEIGHT))
        self.font1 = pygame.font.Font(None, 128)
        self.mapSize = MAP_SIZE
        self.cellSize = CELL_SIZE
        self.pieceSize = PIECE_SIZE
        self.numMap = {}
        self.InitNumMap()
        self.map = Map(self.WIDTH, self.HEIGHT, self.mapSize, self.Pos2Num)
        self.players = {"white": Player(self.map, "white"), "black": Player(self.map, "black")}
        self.players["white"].MovementCacheUpdate(self.map)
        self.availablePos = []
        self.selected = None

    def InitNumMap(self):
        num = 1
        for row in range(self.mapSize):
            for col in range(self.mapSize):
                if (row + col) % 2 == 1:
                    self.numMap[(row,col)] = num
                    num += 1

    def Pos2Num(self, pos):
        return self.numMap.get(pos,None)

    def JudgePos(self, inputPos) -> tuple:
        pos = (int((inputPos[1] - self.map.pos[1]) // self.cellSize + self.mapSize / 2), int((inputPos[0] - self.map.pos[0]) // self.cellSize + self.mapSize / 2))
        cell = self.map.GetCell(pos)
        if cell and cell.color != "blank":
            self.selected = cell if self.selected != cell and self.map.turn == cell.color and self.players[cell.color].haveAvailable == cell.isAvailable and cell.isMovable else None
            self.availablePos = []
            if self.selected == None:
                return pos
            self.availablePos.append(pos)
            for pos_ in self.players[cell.color].movementCache[cell]:
                self.availablePos.append(pos_)
        else:
            if pos in self.availablePos:
                self.selected.Move(self.map, pos, self.players)
                self.availablePos = []
                if not self.selected.isJumping:
                    self.selected = None
                else:
                    for pos_ in self.selected.Find(self.map,self.selected.pos):
                        self.availablePos.append(pos_)
        return pos

    def Render(self):
        self.screen.fill("#d49349")
        for row in range(self.mapSize):
            for col in range(self.mapSize):
                cellPos = (self.map.pos[0] - (self.mapSize / 2 - col) * self.cellSize, self.map.pos[1] - (self.mapSize / 2 - row) * self.cellSize)
                pygame.draw.rect(self.screen, "#e6e6e6" if ( row + col ) % 2 == 0 else "black", (cellPos[0], cellPos[1], self.cellSize, self.cellSize), 0)
                if ( row + col ) % 2 == 1:
                    if (row,col) in self.availablePos:
                        pygame.draw.rect(self.screen, "#4fa5f0", (cellPos[0], cellPos[1], self.cellSize, self.cellSize), 4)
                    cell = self.map.GetCell((row,col))
                    if isinstance(cell, Piece):
                        pygame.draw.circle(self.screen, "#e53636" if cell.color == "black" else "#f1f1f1", (cellPos[0] + self.cellSize / 2, cellPos[1] + self.cellSize / 2), self.pieceSize / 2, 0)
                        if cell.isKing:
                            pygame.draw.circle(self.screen, "#f1f1f1" if cell.color == "black" else "#e53636", (cellPos[0] + self.cellSize / 2, cellPos[1] + self.cellSize / 2), self.pieceSize / 4, 0)
        if self.map.winner != None:
            textSurf = self.font1.render("Winner:"+self.map.winner,True,"#e3b24f")
            textRect = textSurf.get_rect(center = self.map.pos)
            self.screen.blit(textSurf,textRect)
    
game = Game()
pygame.display.set_caption("Draughts")
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            game.JudgePos(pygame.mouse.get_pos())

    game.Render()
    pygame.display.update()
    clock.tick(60)