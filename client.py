import pygame
import pygame_menu
import sys
import socket
from tcpbysize import recv_by_size, send_with_size
import select
from Player import Player
from Bullet import Bullet
from clean_up import *
from diffie_hellman import DIFFIEHELLMAN
from AES import ENCRYPTION

WIDTH = 1540
HEIGHT = 800
SERVER_IP = "192.168.1.44"


def update_game(screen, background, bullets, playerG, sock):
    screen.blit(background, (0, 0))
    # sends the bullet if it got to the end of the screen
    for bullet in bullets:
        if bullet.send_it:
            send_with_size(sock, f"BULL~{bullet.rect.centerx}~{bullet.rect.width}~{bullet.way_length}", None)
            bullet.kill()

    bullets.draw(screen)
    playerG.draw(screen)
    playerG.update(screen)
    bullets.update()


def game(game_sock, screen, is_client, other_addr):

    def return_to_menu(is_won):
        return "", is_won

    def exit_game(is_won):
        return "exit", is_won

    won_menu = pygame_menu.Menu("Exit Screen", WIDTH, HEIGHT, theme=pygame_menu.themes.THEME_DARK)
    won_menu.add.label("WINNER WINNER CHICKEN DINER!!!")
    won_menu.add.button("Return to menu", return_to_menu, 1)
    won_menu.add.button("Exit", exit_game, 1)

    lost_menu = pygame_menu.Menu("Exit Screen", WIDTH, HEIGHT, theme=pygame_menu.themes.THEME_DARK)
    won_menu.add.label("LOST :(")
    lost_menu.add.button("Return to menu", return_to_menu, 0)
    lost_menu.add.button("Exit", exit_game, 0)

    clock = pygame.time.Clock()

    if is_client is True:
        try:
            game_sock.connect((other_addr, 42000))
            print("connected")
        except Exception as e:
            print(e)
    else:
        game_sock, player_addr = game_sock.accept()
        print("connected")

    playerG = pygame.sprite.Group()
    player = Player()
    playerG.add(player)

    bullets = pygame.sprite.Group()

    want_shoot = 0
    pressed = False
    time_pressed = 0
    time_val = 0

    background = pygame.Surface((WIDTH, HEIGHT)).convert()
    background.fill((255, 0, 0))

    in_game = True
    lost = False
    won = False

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        game_sock.setblocking(False)
        ready = select.select([game_sock], [], [], 0)

        # if player is playing
        if in_game:
            update_game(screen, background, bullets, playerG, game_sock)

            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                pressed = True
                if time_pressed % 30 == 0 and want_shoot < player.bullets:
                    want_shoot += 1
                    player.delete_ammo()
                time_pressed += 1

            elif pressed:
                if want_shoot > 0:
                    bullets.add(player.create_bullet(want_shoot))
                pressed = False
                want_shoot = 0
                time_pressed = 0
                time_val = 0

            else:
                time_val += 1
                if time_val == 30:
                    player.add_ammo()
                    time_val = 0

            if ready[0]:
                data = recv_by_size(game_sock, None)
                if data == "LOST":
                    in_game = False
                    won = True
                else:
                    split_data = data.split("~")
                    bullets.add(Bullet(int(split_data[1]), 0, int(split_data[2]), 'down', int(split_data[3])))

            collide_bullet = pygame.sprite.spritecollideany(player, bullets)
            if collide_bullet:
                player.life -= collide_bullet.rect.width / 10 - 1
                if player.life < 1:
                    lost = True
                    send_with_size(game_sock, "LOST", None)
                    in_game = False
                collide_bullet.kill()

        # if player lost
        elif lost:
            game_sock.close()
            return False
        # if player won
        elif won:
            game_sock.close()
            return True

        pygame.display.update()
        clock.tick(60)


def starting_menu(srv_sock, srv_ip, aes):

    def check_user():
        send_with_size(srv_sock, f"USRN~{username.get_value()}", aes, True)
        prot_recv = recv_by_size(srv_sock, aes, True).split('~')
        if prot_recv[0] == "ERRR":
            # no such user
            login_menu._open(new_user_menu)
        else:
            send_with_size(srv_sock, f"PSSW~{username.get_value()}~{password.get_value()}", aes, True)
            prot_recv = recv_by_size(srv_sock, aes, True).split('~')
            if prot_recv[0] == "ERRR":
                # error password is not correct
                login_menu.get_current().reset_value()
            else:
                login_menu._open(connect_menu)

    def new_user():
        send_with_size(srv_sock, f"NEWU~{new_username.get_value()}~{new_password.get_value()}", aes, True)
        prot_recv = recv_by_size(srv_sock, aes, True).split('~')
        if prot_recv[0] == "ERRR":
            new_user_menu.reset_value()
        else:
            new_user_menu.full_reset()

    def connect_player(player_name):
        send_with_size(srv_sock, f"RQST~{player_name}~{username.get_value()}", aes, True)
        draw_menu(waiting_menu, screen, events)

    def want_play(addr):
        send_with_size(srv_sock, f"PLAY~{addr}", aes, True)

    def deny_play():
        send_with_size(srv_sock, "DENY", aes, True)
        login_menu.get_current().close()

    def player_disconnected():
        send_with_size(srv_sock, f"DCON~{username.get_value()}", aes, True)
        recv_by_size(srv_sock, aes, True)

    def return_to_menu():
        login_menu.enable()
        draw_menu(connect_menu, screen, events)

    def exit_game():
        pass

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("DUEL")

    current_time = pygame.time.get_ticks()
    connected_players = []
    players_buttons = []
    label = None

    game_sock = socket.socket()

    clock = pygame.time.Clock()

    did_win = None
    connected = True
    ready = None

    login_menu = pygame_menu.Menu('Welcome', WIDTH, HEIGHT, theme=pygame_menu.themes.THEME_DARK, verbose=False)
    username = login_menu.add.text_input('Username: ')
    password = login_menu.add.text_input("Password: ")
    login_menu.add.button("CONNECT", check_user)

    new_user_menu = pygame_menu.Menu("Create your new user", WIDTH, HEIGHT, theme=pygame_menu.themes.THEME_DARK)
    new_username = new_user_menu.add.text_input('Username: ')
    new_password = new_user_menu.add.text_input("Password: ")
    new_user_menu.add.button("ENTER", new_user)

    connect_menu = pygame_menu.Menu('Choose player', WIDTH, HEIGHT, theme=pygame_menu.themes.THEME_DARK,
                                    onreset=player_disconnected)

    waiting_menu = pygame_menu.Menu('waiting for player', WIDTH, HEIGHT, theme=pygame_menu.themes.THEME_DARK)

    request_menu = pygame_menu.Menu('player game request', WIDTH, HEIGHT, theme=pygame_menu.themes.THEME_DARK,
                                    onclose=deny_play)

    won_menu = pygame_menu.Menu("Exit Screen", WIDTH, HEIGHT, theme=pygame_menu.themes.THEME_DARK)
    won_menu.add.label("WINNER WINNER CHICKEN DINER!!!")
    won_menu.add.button("Return to menu", return_to_menu, 1)
    won_menu.add.button("Exit", exit_game, 1)

    lost_menu = pygame_menu.Menu("Exit Screen", WIDTH, HEIGHT, theme=pygame_menu.themes.THEME_DARK)
    won_menu.add.label("LOST :(")
    lost_menu.add.button("Return to menu", return_to_menu, 0)
    lost_menu.add.button("Exit", exit_game, 0)

    arrow = pygame_menu.widgets.LeftArrowSelection()

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        if not connected:
            srv_sock = socket.socket()
            try:
                srv_sock.connect((srv_ip, 42069))
                print(f'Connect succeeded {srv_ip}')
                connected = True
            except Exception as e:
                print(f'Error while trying to connect.  Check ip or port -- {srv_ip}')
                print(e)

        if type(srv_sock) is socket.socket:
            # srv_sock.setblocking(False)
            ready = select.select([srv_sock], [], [], 0)

        if connected and not login_menu.is_enabled():
            if did_win:
                draw_menu(won_menu, screen, events)
            else:
                draw_menu(lost_menu, screen, events)

        # if getting a sudden message from server
        if login_menu.get_current() != waiting_menu and ready[0]:
            serv_recv = recv_by_size(srv_sock, aes, True)
            connection = serv_recv.split('~')
            # player wants to connect with you
            if connection[0] == "CONC":
                request_menu.add.label(f"playing request from {connection[1]}")
                request_menu.add.button("play", want_play, connection[2])
                request_menu.add.button("deny", deny_play)
                login_menu.get_current()._open(request_menu)
                current_time = pygame.time.get_ticks()

            elif connection[0] == "ACPT":
                srv_sock.close()
                connected = False
                login_menu.disable()
                did_win = game(game_sock, screen, True, connection[1])

        # if in a menu
        elif login_menu.is_enabled():
            draw_menu(login_menu, screen, events)

            # draw arrow on every widget on screen
            if login_menu.get_current().get_selected_widget():
                arrow.draw(screen, login_menu.get_current().get_selected_widget())

            # if connect_menu is displayed
            if login_menu.get_current() == connect_menu:

                time_passed = pygame.time.get_ticks() - current_time
                # sends a request to server for every connected player every second
                if time_passed % 100 == 0:
                    send_with_size(srv_sock, f"USR2", aes, True)
                    connected_players = recv_by_size(srv_sock, aes, True).split('~')

                # if there are no other connected players
                if len(connected_players) < 3 or (len(connected_players) > 1 and connected_players[0] == "ERRR"):
                    # removing any button of a player that is on the screen
                    for button in players_buttons:
                        connect_menu.remove_widget(button)
                    players_buttons = []
                    if len(connect_menu.get_widgets()) == 0:
                        label = connect_menu.add.label("no players connected in your network :(")
                    connect_menu.force_surface_update()

                # if there are connected players
                else:

                    # erase label
                    if label is not None:
                        connect_menu.remove_widget(label)
                        connect_menu.force_surface_update()
                        label = None

                    for name in connected_players[1:]:
                        # if the connected player is not the current player
                        if name != username.get_value() and name not in players_buttons:
                            connect_menu.add.button(f"{name}", connect_player, name, button_id=name)
                            players_buttons.append(name)
                            connect_menu.force_surface_update()

                    # erasing buttons with players who not connected
                    for button in players_buttons:
                        if button not in connected_players[1:]:
                            connect_menu.remove_widget(button)
                            players_buttons.remove(button)
                            connect_menu.force_surface_update()

            # when waiting for response for playing request
            elif login_menu.get_current() == waiting_menu and ready[0]:
                is_connected = recv_by_size(srv_sock, aes, True).split('~')
                print(is_connected)

                # if player accepted request playing
                if is_connected[0] == "ACPT":
                    srv_sock.close()
                    connected = False
                    game_sock.bind(('0.0.0.0', 42000))
                    game_sock.listen(1)
                    login_menu.close()
                    did_win = game(game_sock, screen, False, is_connected[2])

                elif is_connected[0] != "CONC":
                    waiting_menu.close()

        pygame.display.update()
        clock.tick(60)


def main(ip):
    sock = socket.socket()
    port = 42069
    connected = False

    dp_hellman = DIFFIEHELLMAN()
    private_a = dp_hellman.get_private_number()
    public_num = dp_hellman.get_public_number(private_a)

    try:
        sock.connect((ip, port))
        print(f'Connect succeeded {ip} : {port}')
        connected = True
    except Exception as e:
        print(f'Error while trying to connect.  Check ip or port -- {ip} : {port}')
        print(e)

    if connected:
        # encryption initiation
        send_with_size(sock, str(public_num), None)
        public_num_b = int(recv_by_size(sock, None))
        private_key = dp_hellman.get_private_key(public_num_b, private_a)
        aes = ENCRYPTION(private_key)

        starting_menu(sock, ip, aes)

    sock.close()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main(SERVER_IP)
