from streamlit import audio, balloons, button, columns, data_editor, expander, markdown, rerun, session_state, set_page_config, sidebar, tabs, toast, write
from Answers.colorize import colorize_noun
from Sidebar.appSidebar import AppSidebar
from Answers.answers import save_results
from Audio_gen.generate_audio import generate_audio, generate_audios
from pathlib import Path
from time import sleep
from mutagen.mp3 import MP3
from Quiz_tab.init import init_session_state
def main():
    set_page_config(page_title="Lingua", page_icon="🐦", layout="wide", initial_sidebar_state="expanded")
    init_session_state()
    sidebar_manager = AppSidebar()
    if session_state.uploaded_file_data is None:
        from Files.Upload import file_upload_dialog
        if sidebar.button("Upload", icon="📂", use_container_width=True):
            file_upload_dialog()
    else:
        with sidebar:
            left_button, right_button = columns(2, gap="small")
            if left_button.button("🗑️Clear", use_container_width=True):
                    session_state.flashcards_df = None
                    session_state.uploaded_file_data = None
                    session_state.success_value = False
                    session_state.Results.clear()
                    rerun()
            if right_button.button("🪣Reset", on_click=lambda: session_state.Results.clear(), use_container_width=True):
                    session_state.flashcard_index = 0
                    save_results()
                    rerun()
    if "flashcards_df" not in session_state or session_state.flashcards_df is None:
        from Files.Handle_file_upload import Handle_file_upload
        session_state.flashcards_df = Handle_file_upload(session_state.uploaded_file_data, session_state.success_value)
        if session_state.flashcards_df is not None:
            session_state.flashcards_df = session_state.flashcards_df.iloc[::-1].reset_index(drop=True)
            session_state.original_flashcards_df = session_state.flashcards_df.copy()
            try:
                generate_audios(session_state.flashcards_df)
            except Exception as e:
                toast(f"Error generating audio files: {e}", icon="🔊")
    if session_state.flashcards_df is not None:
        with sidebar:
            left_button, right_button = columns(2, gap="small")
            current_index = session_state.flashcard_index if session_state.flashcard_index < len(session_state.flashcards_df ) else 0
            if not session_state.flashcards_df.empty: flashcard = session_state.flashcards_df.iloc[current_index]
            total_flashcards = len(session_state.flashcards_df)
            with left_button:
                if button("✖", key="wrong_button", use_container_width=True, type="primary" if any(result[0] == flashcard['Source'] and not result[2] for result in session_state.Results) else "secondary") and not session_state.show_wrongs:
                    session_state.Results = [result for result in session_state.Results if result[1] != flashcard['Source']]
                    session_state.Results.append([int(current_index)+1, flashcard['Source'], flashcard['Target'], False])
                    session_state.flashcard_index = (current_index + 1) % total_flashcards
                    save_results()
                    markdown(f"{colorize_noun(flashcard)}", unsafe_allow_html=True)
                    audio_path = Path(f"cached_audios/{flashcard['Target']}.mp3")
                    if not audio_path.exists():
                        audio_path = generate_audio(flashcard["Target"])
                    with open(audio_path, "rb") as audio_file:
                        audio(audio_file, format="audio/mp3", autoplay=True)
                    sleep(MP3(audio_path).info.length + 1)
                    rerun()
            with right_button:
                if button("✔", key="correct_button", use_container_width=True, type="  " if any(result[0] == flashcard['Source'] and result[2] for result in session_state.Results) else "secondary") and not session_state.show_wrongs:
                    session_state.Results = [result for result in session_state.Results if result[1] != flashcard['Source']]
                    session_state.Results.append([int(current_index)+1, flashcard['Source'], flashcard['Target'], True])
                    session_state.flashcard_index = (current_index + 1) % total_flashcards
                    markdown(f"{colorize_noun(flashcard)}", unsafe_allow_html=True)
                    audio_path = Path(f"cached_audios/{flashcard['Target']}.mp3")
                    if not audio_path.exists():
                        audio_path = generate_audio(flashcard["Target"])
                    with open(audio_path, "rb") as audio_file:
                        audio(audio_file, format="audio/mp3", autoplay=True)
                    sleep(MP3(audio_path).info.length + 1)
                    rerun()
            with left_button:
                if button("⮜", key="prev_button", use_container_width=True, type="primary"):
                    session_state.flashcard_index = (current_index - 1) % total_flashcards
                    rerun()
            with right_button:
                if button("⮞", key="next_button", use_container_width=True, type="primary"):
                    session_state.flashcard_index = (current_index + 1) % total_flashcards
                    write(session_state.flashcard_index)
                    rerun()
            with expander("Settings", expanded=False, icon="⚙️"):
                left_button, right_button = columns(2, gap="small", vertical_alignment='center')
                session_state.auto_continue = right_button.toggle("⏩", key="auto", value=session_state.auto_continue, help="Auto-continue")
                session_state.Show_all_anwsers = left_button.toggle("🔠", key="show", value=session_state.Show_all_anwsers, help="Learning mode")
                session_state.show_wrongs = left_button.toggle("🔂", key="wrongs", value=session_state.show_wrongs, help="Review mistakes")
            sidebar_manager.get_user_input()
            sidebar_manager.download_results()
        session_state.flashcards_df = session_state.flashcards_df.iloc[[i for i, result in enumerate(session_state.Results) if not result[3]]] if session_state.show_wrongs else session_state.original_flashcards_df.copy()            
        if len(session_state.Results) == total_flashcards and total_flashcards != 0 and not session_state.show_wrongs:
            balloons()
            write("""<br><div style="text-align:center; font-size:50px;"><strong>All the cards are done!🥳🎆</strong><br></div>""", unsafe_allow_html=True)
        else :
            quiz_tab, all_cards = tabs(["🎮 **Quiz**", f"📓 **{session_state.uploaded_file_data.name if not session_state.flashcards_df is None else "All cards"}**"])
            with quiz_tab:
                from Quiz_tab.Quiz import Quiz
                Quiz(session_state.flashcards_df)
                with sidebar:
                    if session_state.flashcards_df is not None: 
                        with sidebar.expander("Timer", icon="⏱️"):
                            sidebar_manager.timer()
                        left_button, right_button = sidebar.columns([1, 1], vertical_alignment="bottom")
                        if len(session_state.Results) > 1 or not session_state.show_wrongs:
                            try:
                                page_input = left_button.number_input("Page :", min_value=1, max_value=len(session_state.flashcards_df), step=1, value=session_state.flashcard_index+1, key="page_input")
                            except:
                                page_input=0
                            if session_state.flashcard_index != page_input - 1:
                                session_state.flashcard_index = page_input - 1
                                rerun()
                        if not session_state.Show_all_anwsers and not session_state.show_wrongs:
                            with right_button.popover(f"📋 ", use_container_width=True):
                                write("Unanswerd :" + " | ".join([str(i + 1) for i, flashcard in session_state.flashcards_df.iterrows() if not any(result[1] == flashcard['Source'] for result in session_state.Results)]))
            with all_cards:
                from Flashcards.Viewer import viewer_table
                viewer_table(sidebar_manager, session_state.flashcards_df)
        if not session_state.Show_all_anwsers and not session_state.show_wrongs:
            with expander(
                f"👍🏼 {((wval := sum(r[3] == True for r in session_state.Results)) / (l := len(session_state.Results) or 1) * 100):.1f}% - {wval} ||"
                f"👎🏼 {((wval := sum(r[3] == False for r in session_state.Results)) / l * 100):.1f}% - {wval}", expanded=True):
                if len([r for r in session_state.Results if r[3] == False]) > 0: data_editor([{'Source : Target': f"{r[0]} - {r[1]} : {r[2]}"} for r in session_state.Results if r[3] == False][::-1], hide_index=True, use_container_width=True)
    else:
        sidebar_manager.get_user_input()
if __name__ == "__main__":
    main()