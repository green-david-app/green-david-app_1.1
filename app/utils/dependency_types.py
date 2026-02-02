from enum import Enum


class DependencyType(Enum):
    # ČASOVÁ
    TEMPORAL_FINISH_TO_START = "finish_to_start"
    TEMPORAL_START_TO_START = "start_to_start"
    TEMPORAL_FINISH_TO_FINISH = "finish_to_finish"
    
    # MATERIÁLOVÁ
    MATERIAL_PRODUCES = "material_produces"
    MATERIAL_SHARES = "material_shares"
    
    # KOMPETENČNÍ
    COMPETENCY_REQUIRES = "competency_requires"
    COMPETENCY_SAME_PERSON = "competency_same"
    
    # LOKAČNÍ
    LOCATION_SEQUENTIAL = "location_sequential"
    LOCATION_EXCLUSIVE = "location_exclusive"
    
    # INFORMAČNÍ
    INFO_PRODUCES = "info_produces"
    INFO_VALIDATES = "info_validates"
