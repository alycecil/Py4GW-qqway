from Py4GWCoreLib import Botting, get_texture_for_model, ModelID, AutoPathing
import PyImGui

BOT_NAME = "Alkar's Concoction Item Getter"
MODULE_NAME = BOT_NAME

OUTPOST_TO_TRAVEL = 654 # Central Transfer Chamber

ALKARS_CONCOCTION = 25739
MOVE_TO = (10, -831)

bot = Botting(BOT_NAME)


def Routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.Map.Travel(OUTPOST_TO_TRAVEL)
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Wait.ForTime(333)
    bot.Items.Deposit(ALKARS_CONCOCTION)
    bot.Wait.ForTime(100)
    bot.Move.XY(MOVE_TO[0], MOVE_TO[1])
    bot.Move.XYAndDialog(-5.00, -911.00, 0x835C05)
    bot.Wait.ForTime(333)
    bot.Items.Deposit(ALKARS_CONCOCTION)
    bot.States.JumpToStepName(f"[H]{BOT_NAME}_loop_2")


bot.SetMainRoutine(Routine)


def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored(f"{BOT_NAME} from Central Transfer Chamber", title_color.to_tuple_normalized())
    ImGui.pop_font()
    PyImGui.spacing()
    PyImGui.separator()
    # Description
    PyImGui.text("Single Account")
    PyImGui.end_tooltip()


def main():

    bot.Update()
    bot.UI.draw_window()


if __name__ == "__main__":
    main()
