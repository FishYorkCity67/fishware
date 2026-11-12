#pragma once

// FishWare: gemeinsame Fisch-Logik fuer Pass, Einstellungen und Aquarium-App.
// Header-only (static inline), damit FAPs keine neuen API-Symbole brauchen.

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// settings.h hat selbst kein extern "C", daher hier drin einbinden
#include "settings.h"

typedef enum {
    FishSpeciesGuppy, // Level 1-4
    FishSpeciesClown, // Level 5-9
    FishSpeciesPuffer, // Level 10-14
    FishSpeciesRay, // Level 15-19
    FishSpeciesSword, // Level 20-24
    FishSpeciesShark, // Level 25+
    FishSpeciesCount,
} FishSpecies;

typedef enum {
    FishHungerFull, // < 8 h seit Fuetterung
    FishHungerPeckish, // 8-24 h
    FishHungerStarving, // > 24 h oder nie gefuettert
} FishHunger;

// Aquarium-App (FAP) und ihr Eintrag im Hauptmenue
#define FISH_AQUARIUM_PATH "/ext/apps/Games/fish_aquarium.fap"

#define FISH_FULL_SECONDS    (8UL * 60 * 60)
#define FISH_PECKISH_SECONDS (24UL * 60 * 60)

static inline FishSpecies fish_species_for_level(uint8_t level) {
    if(level >= 25) return FishSpeciesShark;
    if(level >= 20) return FishSpeciesSword;
    if(level >= 15) return FishSpeciesRay;
    if(level >= 10) return FishSpeciesPuffer;
    if(level >= 5) return FishSpeciesClown;
    return FishSpeciesGuppy;
}

// Level, ab dem die naechste Art erreicht wird (0 = schon die groesste)
static inline uint8_t fish_next_species_level(uint8_t level) {
    if(level < 5) return 5;
    if(level < 10) return 10;
    if(level < 15) return 15;
    if(level < 20) return 20;
    if(level < 25) return 25;
    return 0;
}

static inline const char* fish_species_name(FishSpecies species) {
    switch(species) {
    case FishSpeciesGuppy:
        return "Guppy";
    case FishSpeciesClown:
        return "Clownfish";
    case FishSpeciesPuffer:
        return "Pufferfish";
    case FishSpeciesRay:
        return "Stingray";
    case FishSpeciesSword:
        return "Swordfish";
    case FishSpeciesShark:
        return "Shark";
    default:
        return "Fish";
    }
}

static inline FishHunger fish_hunger(uint32_t now, uint32_t fed_ts) {
    if(fed_ts == 0 || now < fed_ts) return FishHungerStarving;
    uint32_t since = now - fed_ts;
    if(since < FISH_FULL_SECONDS) return FishHungerFull;
    if(since < FISH_PECKISH_SECONDS) return FishHungerPeckish;
    return FishHungerStarving;
}

static inline const char* fish_hunger_name(FishHunger hunger) {
    switch(hunger) {
    case FishHungerFull:
        return "Full";
    case FishHungerPeckish:
        return "Peckish";
    default:
        return "Hungry";
    }
}

static inline const char* fish_name(void) {
    return momentum_settings.fish_name[0] ? momentum_settings.fish_name : "Bubbles";
}

#ifdef __cplusplus
}
#endif
