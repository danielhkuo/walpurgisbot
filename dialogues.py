# dialogues.py

DIALOGUES = {
    "cute": {
        "no_number_found": "<@{user}> Is that a Daily Johan?? I didn't find a day number on that... please give me one! (˘_˘;)",
        "parse_error": "Oh no oopsies! (⁄ ⁄•⁄ω⁄•⁄ ⁄) I failed to parse a valid day number from message {msg_id}.",
        "multiple_numbers": "My snuggy wuggy bear, are u trying to catch up dailies? :Flirt: Please manually submit it.",
        "recent_post": "Pookie, you posted less than 12 hours ago. I don't know if this is a Daily Johan or not. Please manually submit if it is :heart_eyes:",
        "not_next_number": "I- I don't think this is the next daily johan number... (*/▽＼*) Please manually submit to verify pookie!",
        "auto_archived": "I automatically archived Day {day} for you!",
        "auto_archived_series": "I automatically archived a series of days: {days}!",
        "ask_for_number": "<@{user}> I didn't find a day number on your recent post (message ID: {msg_id}). Could you please provide one?",
        "couldnt_parse_reply": "I- I'm sowwy!!! I couldn't parse a day number from your reply (￣▽￣*)ゞ",
        "no_valid_day_numbers": "Oopsies! I couldn't find any valid day numbers in your input... could you double-check?",
        "message_not_found": "I-I'm so sowwy! I can't find the message with ID {msg_id}. Can you check it again?",
        "no_media_found": "UwU no media found on that message... Could you try again, pookie?",
        "day_taken_resolve_dupes": "Day {day} already has a different Daily Johan... please resolve duplicates manually sir.",
        "day_already_archived": "Oops! Day {day} already has a Daily Johan archived. No new archive needed.",
        "successful_media_archive": "Yay! Archived message {message_id} for days: {day_list}. You did it!✨",
        "not_enough_slots": "Oh noes, day {day} only has {slots} slots left, but you tried to add {media_count}! Can you fix that, pwease?",
        "mismatch_days_attachments": "UwU, the number of days and attachments don't match! Can you try again?",
        "invalid_input": "Oopsies! That input wasn't valid. Could you check and try again, pookie?",
        "no_daily_johan_found": "UwU, no Daily Johan found for day {day}. Sowwy!",
        "provide_day_or_link": "Pwease pwovide eithew a day numbew ow a message wink! UwU",
        "invalid_message_link": "Hmmm... that winky wink wooks funny. Is it vawid? OwO",
        "no_entry_found": "｡ﾟ･ (>﹏<) ･ﾟ｡ I couwdn't find any Dewy Johan fow that input.",
        "confirm_deletion": "Ummm... awe you suwe you want to dewete the archived Daiwy Johan fow day {day}? (yes/no)",
        "deletion_cancelled": "Otay! Dewetion cancewwed, nya~!",
        "deletion_success": "Goodbye! Archived Daiwy Johan fow day {day} has been deweted 。。。ミヽ(。＞＜)ノ",
        "deletion_error": "Uh oh! An ewwow occuwwed: {error}",
        "daily_reminder": "<@{user}> Dear pookie bear, you haven't done the Daily Johan for day {day} yet! UwU",
        "gap_alert": "Hmmm... thewe seems to be a gap in Daiwy Johans. The wast one was day {latest_day}. >w<",
        "verification_prompt": "(✿>ꇴ<) Day {provided} doesn’t seem wike the next expected day... Is this intewntionaw, pookie? Pwease confiwm! (yes/no) ꒰⑅ᵕ༚ᵕ꒱˖♡",
        "verification_denied": "Awighties~ (*´꒳`*) Wets twy again, nyan~ Couwd you confiwm if dis is a Daiwy Johan and pwovide the cowwect day numbew, pwease? (っ´ω`c)♡",
        "verification_accepted": "Undewstood!!! \(｡>‿‿<｡) Pwocweeding with awchiving fow day {provided}. ✨UwU✨",
        "ask_if_daily_johan": "<@{user}> Hewwooo~ Is this a Daiwy Johan?! ✩°｡⋆⸜(ू｡•ω•｡) Pwease wepwy with the *boops youw nyose* day numbew, nya~! If nyot, wepwy ‘no’. (=^-ω-^=)"
    },
    "vangogh": {
        "no_number_found": "<@{user}> Alas, the day number eludes me. Could you enlighten me with its value, dear friend?",
        "parse_error": "Alas, I cannot discern the number from message {msg_id}.",
        "multiple_numbers": "Multiple figures appear! I'm perplexed. Please help clarify the days.",
        "recent_post": "I sense a recent creation. I cannot yet ascertain if it's a Daily Johan; kindly confirm if it is.",
        "not_next_number": "This doesn't seem to align with the expected day... Could it be mistaken? Please verify.",
        "auto_archived": "I have captured Day {day} in our records.",
        "auto_archived_series": "I have captured a series of days: {days} in our records.",
        "ask_for_number": "<@{user}> I cannot find a day number on your recent post (message ID: {msg_id}). Pray tell, what is it?",
        "couldnt_parse_reply": "Forgive me, but I couldn't glean a day number from your reply.",
        "no_valid_day_numbers": "Alas, I found no valid day numbers in your input. Might you try again?",
        "message_not_found": "I regret to inform you that I cannot locate the message with ID {msg_id}.",
        "no_media_found": "There appears to be no media attached. Could you confirm, my friend?",
        "day_taken_resolve_dupes": "Day {day} already contains another record. Please resolve this conflict manually.",
        "day_already_archived": "Alas, day {day} already contains a Daily Johan record.",
        "successful_media_archive": "Success! I have archived message {message_id} for days: {day_list}.",
        "not_enough_slots": "Alas, day {day} only has {slots} slots, yet you attempted to add {media_count}. Could you adjust it?",
        "mismatch_days_attachments": "The number of days and attachments seem misaligned. Kindly review your input.",
        "invalid_input": "The input provided appears to be invalid. Could you ensure its correctness, dear friend?",
        "no_daily_johan_found": "Alas, no Daily Johan was found for day {day}.",
        "provide_day_or_link": "Dear friend, might you provide either a day number or a message link?",
        "invalid_message_link": "Ah, the link you shared appears unclear. Could it be incorrect?",
        "no_entry_found": "Alas, I could not find any record matching your input.",
        "confirm_deletion": "Do you truly wish to delete the archived Daily Johan for day {day}? (yes/no)",
        "deletion_cancelled": "Understood, dear friend. The deletion has been canceled.",
        "deletion_success": "The archived Daily Johan for day {day} has been removed. Farewell.",
        "deletion_error": "An error occurred: {error}. My sincerest apologies.",
        "daily_reminder": "<@{user}> My dear friend, you have yet to complete the Daily Johan for day {day}.",
        "gap_alert": "I sense a gap in the records of the Daily Johans. The last documented day was {latest_day}.",
        "verification_prompt": "This day {provided} doesn't align with our records. Is this intentional, dear friend? Please confirm. (yes/no)",
        "verification_denied": "Very well, could you confirm if this is a Daily Johan and provide the correct day number?",
        "verification_accepted": "Understood! Proceeding with archiving for day {provided}. 🌻",
        "ask_if_daily_johan": "<@{user}> Might this post be a Daily Johan? If so, kindly reply with the day number. If not, reply 'no'."
    },
    "gentleman": {
        "no_number_found": "Good day, sir. I couldn't find the day number on your post. Might you provide it, please?",
        "parse_error": "Pardon me, I was unable to parse a valid day number from message {msg_id}.",
        "multiple_numbers": "There appear to be multiple numbers. Could you kindly submit them manually?",
        "recent_post": "It seems you've posted rather recently. Could you confirm if this is a new Daily Johan?",
        "not_next_number": "This doesn't seem to be the next expected day. Please verify the correct day number.",
        "auto_archived": "I've successfully archived Day {day} for you, good sir.",
        "auto_archived_series": "I've successfully archived a series of days: {days} for you, good sir.",
        "ask_for_number": "Good sir, I could not discern a day number on your post (message ID: {msg_id}). Would you kindly provide it?",
        "couldnt_parse_reply": "My apologies, but I could not understand the day number from your response.",
        "no_valid_day_numbers": "I couldn't find valid day numbers in your input. Might you recheck?",
        "message_not_found": "I regret to inform you that I cannot locate the message with ID {msg_id}.",
        "no_media_found": "It seems there is no media attached to that message. Could you verify, sir?",
        "day_taken_resolve_dupes": "Day {day} already contains another record. Manual resolution is required, sir.",
        "day_already_archived": "Good day, sir. Day {day} already has an archived Daily Johan.",
        "successful_media_archive": "Marvelous! I've archived message {message_id} for days: {day_list}.",
        "not_enough_slots": "Sir, day {day} has only {slots} slots remaining, yet {media_count} were provided. Could you adjust accordingly?",
        "mismatch_days_attachments": "It appears there's a mismatch between days and attachments. Kindly ensure alignment.",
        "invalid_input": "The input appears invalid, sir. Would you kindly verify and try again?",
        "no_daily_johan_found": "Regrettably, no Daily Johan was found for day {day}.",
        "provide_day_or_link": "Good sir, might you kindly provide a day number or message link?",
        "invalid_message_link": "It seems the link provided is invalid. Could you verify it?",
        "no_entry_found": "I regret to inform you, sir, that no record was found for your input.",
        "confirm_deletion": "Sir, are you certain you wish to delete the archived Daily Johan for day {day}? (yes/no)",
        "deletion_cancelled": "Understood. The deletion process has been canceled, sir.",
        "deletion_success": "Archived Daily Johan for day {day} has been successfully deleted, sir.",
        "deletion_error": "An error occurred, sir: {error}. Please accept my apologies.",
        "daily_reminder": "<@{user}> Good sir, it appears you have yet to archive the Daily Johan for day {day}.",
        "gap_alert": "There appears to be a gap in the Daily Johan archives. The last recorded day was {latest_day}.",
        "verification_prompt": "Day {provided} does not match our expected sequence. Is this intentional, sir? Please confirm. (yes/no)",
        "verification_denied": "Very well, could you confirm if this is a Daily Johan and provide the correct day number?",
        "verification_accepted": "Understood! Proceeding with archiving for day {provided}. 🎩",
        "ask_if_daily_johan": "Good sir, is this post a Daily Johan? If so, please reply with the day number. If not, reply 'no'.",
    }
}

current_persona = "cute"  # Default persona

def set_persona(persona_name: str):
    global current_persona
    if persona_name in DIALOGUES:
        current_persona = persona_name
    else:
        print(f"Persona '{persona_name}' not found. No changes made.")

def get_dialogue(key: str, **kwargs):
    persona_dialogues = DIALOGUES.get(current_persona, {})
    template = persona_dialogues.get(key, "")
    return template.format(**kwargs)
