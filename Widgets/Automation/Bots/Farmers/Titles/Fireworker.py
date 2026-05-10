from Py4GWCoreLib import Botting, get_texture_for_model, ModelID
import PyImGui

#QUEST TO INCREASE SPAWNS 
BOT_NAME = "Fireworks Party Helper"
MODULE_NAME = BOT_NAME

OUTPOST_TO_TRAVEL = 642 # eotn

bot = Botting(BOT_NAME)
                
def Routine(bot: Botting) -> None:
    bot.States.AddHeader(BOT_NAME)
    bot.Templates.Aggressive(enable_imp=False)
    bot.Party.LeaveParty()
    bot.States.AddHeader(f"{BOT_NAME}_loop")
    bot.Map.Travel(OUTPOST_TO_TRAVEL)
    bot.Wait.ForTime(1000)
    bot.Map.TravelGH()
    bot.Wait.ForTime(1000)
    bot.Items.UseItem(ModelID.Crate_Of_Fireworks.value)
    bot.Wait.ForTime(1000)
    bot.States.JumpToStepName(f"[H]{BOT_NAME}_loop_2")

bot.SetMainRoutine(Routine)

def tooltip():
    import PyImGui
    from Py4GWCoreLib import ImGui, Color
    PyImGui.begin_tooltip()

    # Title
    title_color = Color(255, 200, 100, 255)
    ImGui.push_font("Regular", 20)
    PyImGui.text_colored("Crate of Fireworks Bot", title_color.to_tuple_normalized())
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
