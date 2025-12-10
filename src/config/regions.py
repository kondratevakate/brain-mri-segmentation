# Region whitelists for pairwise analysis (dataset-agnostic)

# Cortical DKT regions (18 labels, L/R)
CORTICAL_LABELS = [
    1002, 1006, 1007, 1008, 1012, 1014, 1028, 1030, 1035,
    2002, 2006, 2007, 2008, 2012, 2014, 2028, 2030, 2035,
]
CORTICAL_LABEL_NAMES = {
    1002: "Caudal Anterior Cingulate L",
    1006: "Entorhinal Cortex L",
    1007: "Fusiform Gyrus L",
    1008: "Inferior Parietal L",
    1012: "Insula L",
    1014: "Lateral Orbitofrontal L",
    1028: "Medial Orbitofrontal L",
    1030: "Superior Frontal L",
    1035: "Superior Temporal L",
    2002: "Caudal Anterior Cingulate R",
    2006: "Entorhinal Cortex R",
    2007: "Fusiform Gyrus R",
    2008: "Inferior Parietal R",
    2012: "Insula R",
    2014: "Lateral Orbitofrontal R",
    2028: "Medial Orbitofrontal R",
    2030: "Superior Frontal R",
    2035: "Superior Temporal R",
}

# Subcortical labels (thalamus/caudate/putamen/pallidum/accumbens/ventral DC/hippocampus/amygdala)
SUBCORTICAL_LABELS = [
    10, 49,   # Thalamus L/R
    11, 50,   # Caudate L/R
    12, 51,   # Putamen L/R
    13, 52,   # Pallidum L/R
    17, 53,   # Hippocampus L/R
    18, 54,   # Amygdala L/R
    26, 58,   # Accumbens L/R
    28, 60,   # Ventral DC L/R
]
SUBCORTICAL_LABEL_NAMES = {
    10: "Thalamus L", 49: "Thalamus R",
    11: "Caudate L", 50: "Caudate R",
    12: "Putamen L", 51: "Putamen R",
    13: "Pallidum L", 52: "Pallidum R",
    17: "Hippocampus L", 53: "Hippocampus R",
    18: "Amygdala L", 54: "Amygdala R",
    26: "Accumbens L", 58: "Accumbens R",
    28: "Ventral Diencephalon L", 60: "Ventral Diencephalon R",
}

# Combined 34-region set (cortical + subcortical)
CORTICAL_AND_SUBCORTICAL = CORTICAL_LABELS + SUBCORTICAL_LABELS

# Names for the combined set
CORTICAL_AND_SUBCORTICAL_NAMES = {
    **CORTICAL_LABEL_NAMES,
    **SUBCORTICAL_LABEL_NAMES,
}

# Default whitelist
DEFAULT_WHITELIST = CORTICAL_LABELS
