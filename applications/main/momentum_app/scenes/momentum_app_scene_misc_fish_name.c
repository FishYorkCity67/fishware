#include "../momentum_app.h"

// FishWare: Namen des Fisches festlegen

enum TextInputIndex {
    TextInputResultOk,
};

static void momentum_app_scene_misc_fish_name_text_input_callback(void* context) {
    MomentumApp* app = context;
    view_dispatcher_send_custom_event(app->view_dispatcher, TextInputResultOk);
}

void momentum_app_scene_misc_fish_name_on_enter(void* context) {
    MomentumApp* app = context;
    TextInput* text_input = app->text_input;

    text_input_set_header_text(text_input, "Name your fish");
    text_input_set_minimum_length(text_input, 1);
    text_input_set_result_callback(
        text_input,
        momentum_app_scene_misc_fish_name_text_input_callback,
        app,
        app->fish_name,
        sizeof(app->fish_name),
        false);

    view_dispatcher_switch_to_view(app->view_dispatcher, MomentumAppViewTextInput);
}

bool momentum_app_scene_misc_fish_name_on_event(void* context, SceneManagerEvent event) {
    MomentumApp* app = context;
    bool consumed = false;

    if(event.type == SceneManagerEventTypeCustom) {
        consumed = true;
        if(event.event == TextInputResultOk) {
            strlcpy(
                momentum_settings.fish_name,
                app->fish_name,
                sizeof(momentum_settings.fish_name));
            app->save_settings = true;
            scene_manager_previous_scene(app->scene_manager);
        }
    }

    return consumed;
}

void momentum_app_scene_misc_fish_name_on_exit(void* context) {
    MomentumApp* app = context;
    text_input_reset(app->text_input);
    // Bei Abbruch Eingabe verwerfen
    strlcpy(app->fish_name, fish_name(), sizeof(app->fish_name));
}
