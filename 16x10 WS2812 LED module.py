from machine import Pin
import rp2
import time

@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 =  4 # 16 # 8	# 7 ilość cykli, ile cykli ma trwać stan. Nie ważne, że dochodzi cykl rozkazu - ówzględnione poprzez odjęcie 1
    T2 =  4 #  7 # 7	# 4 ilość cykli, ile cykli ma trwać stan. Nie ważne, że dochodzi cykl rozkazu - ówzględnione poprzez odjęcie 1
    T3 = 13 #  6 # 9	# 5 ilość cykli, ile cykli ma trwać stan. Nie ważne, że dochodzi cykl rozkazu - ówzględnione poprzez odjęcie 1
    T4 = 13 #  4 # 9	# 5 ilość cykli, ile cykli ma trwać stan. Nie ważne, że dochodzi cykl rozkazu - ówzględnione poprzez odjęcie 1
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T1 - 1] # 7
    jmp(not_x, "do_zero")   .side(1)    [T2 - 1] # 4
    jmp("bitloop")          .side(1)    [T3 - 1] # 5
    label("do_zero")
    nop()                   .side(0)    [T4 - 1] # 5
    wrap()
class displayWS2812:
    def __init__(self, datain, foreground, background):
        self.foreground = foreground
        self.background = background
        self.display_array = []
        for i in range(0, 160):
            self.display_array.append(self.background)
        # Create the StateMachine with the ws2812 program, outputting on Pin(din).
        # freq dobrana by był najmniejszy błąd dla różnych typów WS2812 - jaknie zadziała to zabawa zegarem i iloścą cykli
        self.sm = rp2.StateMachine(0, ws2812, freq= 12_500_000, sideset_base=Pin(datain)) # 19_000_000 # 19_000_000 # 12_800_000
        # Start the StateMachine, it will wait for data on its FIFO.
        self.sm.active(1)
        self.show()
    def plot(self, x, y, color = None, show = False):
        if color == None: color = self.foreground
        x = abs(x) % 16		# 0 <= X <= 15
        y = abs(y) % 10		# 0 <= Y <= 9
        pos = x + 16*(9 - y)
        self.display_array[pos] = color
        if show: self.show()
    def unplot(self, x, y, show = False):
        self.plot(x, y, self.background, show)
    def show(self):
        sm_put = self.sm.put
        for led in self.display_array:
            sm_put(led)
        # można wprowadzić przerwę
        time.sleep_us(50)
        # by na pewno pojawił się stan REST na linii DIN WS2812 o czasie trwania 50 us (katalogowo)
    def clear(self):
        for pos in range(0, 160):
            self.display_array[pos] = self.background
        self.show()
#
# --------------------------------------------------------------------------------------
#
class piksel:
    def __init__(self, red, green, blue):
        # r,g,b <= 255
        self.red = abs(red) & 0xFF
        self.green = abs(green) & 0xFF
        self.blue = abs(blue) & 0xFF
        # 32 bitowy atrubut
        self.__rgb32bit__ = (red << 24) | (green << 16) | (blue << 8)
    def get32bit(self):
        return self.__rgb32bit__
    def set32bit(self, rgb32bit):
        self.__rgb32bit__ = abs(rgb32bit) & 0xFFFFFFFF
        self.red   = (self.__rgb32bit__ & 0xFF000000) >> 24
        self.green = (self.__rgb32bit__ & 0xFF0000  ) >> 16
        self.blue  = (self.__rgb32bit__ & 0xFF00    ) >>  8
        return [self.red, self.green, self.blue]
#
# ===================================================================================================
#
#
# Program demo użycia sterowania diodami WS2812 w module 10x16 (160 diod)
# oraz zmiennej typu piksel
#
# Odbijające się piłeczki
#

# inicjalizacja
pin_DIN_WS2812 = 0
kolor_pikselka = piksel(0,0,0).get32bit()   # ustawienie pro forma bo i tak będzie zmieniany - wymagania inicjalizacji modułu
kolor_tla = piksel(1,1,1).get32bit()        # ustawienie pro forma bo i tak będzie zmieniany - wymagania inicjalizacji modułu
# kolor_tla = piksel(0,0,0).get32bit()        # ustawienie pro forma bo i tak będzie zmieniany - wymagania inicjalizacji modułu
ekran = displayWS2812(pin_DIN_WS2812, kolor_pikselka, kolor_tla)
ekran.clear()                               # przygotowanie modułu i wypełnienie tła kolorem: kolor_tla
ekran.background = piksel(0,0,0).get32bit() # ustawienie koloru tla bez wypełniania nim ekranu - piłeczka będzie "wymazywać" tło
#
# Snake
#         
moduly = [
        {'x': 1,'dx': 1,'y':7,'dy':-1, 'y0':6, 'dy0':1, 'nr_koloru':0}, # moduł nr 0
        {'x':14,'dx':-1,'y':2,'dy': 1, 'y0':5, 'dy0':1, 'nr_koloru':1}, # moduł nr 1
        {'x': 4,'dx': 1,'y':6,'dy': 1, 'y0':4, 'dy0':1, 'nr_koloru':2}, # moduł nr 2
        {'x':11,'dx':-1,'y':3,'dy':-1, 'y0':3, 'dy0':1, 'nr_koloru':3}, # moduł nr 3
        {'x': 5,'dx': 1,'y':3,'dy':-1, 'y0':2, 'dy0':1, 'nr_koloru':4}, # moduł nr 1
        {'x':10,'dx':-1,'y':6,'dy': 1, 'y0':1, 'dy0':1, 'nr_koloru':5}, # moduł nr 2
        {'x': 8,'dx': 1,'y':4,'dy':-1, 'y0':0, 'dy0':1, 'nr_koloru':6}  # moduł nr 3
        ]
kolory = [	piksel(64, 0,  0).get32bit(),
            piksel( 0,64,  0).get32bit(),
            piksel( 0, 0,128).get32bit(),
            piksel(32,32, 32).get32bit(),
            piksel(64,64,  0).get32bit(),
            piksel( 0,64,64).get32bit(),
            piksel(64, 0,128).get32bit()
        ]
# tdelay = 0.04			# przerwa dla płynnej animacji ruchu
tdelay = 0.03
# narysowanie
for modul in moduly:
    ekran.plot(modul['x'], modul['y'], kolory[modul['nr_koloru']])
ekran.show()
time.sleep(5)
# animacja  Snake-a
while(1):
    time.sleep(tdelay)
    for modul in moduly:
        ekran.unplot(modul['x'], modul['y'])
#    ekran.show()
    for modul in moduly:
        if modul['x'] == 0 and modul['y'] == modul['y0']:
            nexty = modul['y'] + modul['dy0']
            if nexty < 0 or nexty > 9:
                modul['dy0'] *= -1
            modul['y0'] += modul['dy0']
            modul['y'] = modul['y0']
        nextx = modul['x'] + modul['dx']
        if nextx < 0 or nextx > 15:
            modul['dx'] *= -1
        nexty = modul['y'] + modul['dy']
        if nexty < 0 or nexty > 9:
            modul['dy'] *= -1            
        modul['x'] += modul['dx']
        modul['y'] += modul['dy']
        ekran.plot(modul['x'], modul['y'], kolory[modul['nr_koloru']])
    time.sleep(tdelay)
    ekran.show()
