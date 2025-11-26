# Persona Profile Schema

Consumer research from `data/raw/lavazza/customer-segmentation/2023 03_FR_Consumers Segmentation France.pdf` identifies nine French coffee personas (e.g., Mindful Enthusiast, Habitual Disciplinist, Spontaneous Connector). The `PersonaProfile` schema translates those qualitative insights into a consistent, machine-readable structure that downstream services (retrieval-augmented generation, activation planning, experimentation) can share.

## Conceptual structure

```json
{
  "persona_id": "curious-conoisseurs-fr",
  "segment_name": "Curious Conoisseurs",
  "locale": "fr_FR",
  "source_reference": {
    "document": "2023 03_FR_Consumers Segmentation France.pdf",
    "pages": [
      32,
      58
    ],
    "extraction_notes": "Context pulled from customer segmentation playbook."
  },
  "core_profile_overview": {
    "market_impact": {
      "population_share_percentage": 9.8,
      "value_share_percentage": 13.6,
      "spend_at_home_index": 137
    },
    "identity_summary": {
      "demographics": "Mid-to-older age, urban areas of France. University degree holders, employed as jr. managers or entrepreneurs. Higher income.",
      "psychographics": "Creative type. Always looking for challenge, novelty and change. Quality seekers willing to pay more, especially for convenience."
    },
    "sustainability_attitude": {
        "statement": "I deliberately avoid buying drinks in plastic bottles",
        "index": 103
    },
    "consumption_habits": {
      "at_home": {
        "volume": {
          "average_daily_coffees": 2.9,
          "index": 116
        },
        "behavior_description": "Loves rich aroma/flavor. Drinks for enjoyment or focus. Knowledgeable and explorative with new/lesser known brands. Prefers beans to feel like a barista."
      },
      "out_of_home": {
        "volume": {
          "average_daily_coffees": 2.5,
          "index": 114
        },
        "behavior_description": "Chooses places based on quality and environment. Seeks specific local/heritage brands. Moments of pampering or positive mood shifting."
      }
    },
    "shopping_attitude": {
      "statement": "I usually look for promotions when buying coffee",
      "index": 100
    },
    "innovation_interest": {
      "summary": "High interest in concepts that fit their exploring nature and conscious behavior."
    }
  },
  "demographics": {
    "gender_distribution": {
      "female": {
        "percentage": 52,
        "index": 102
      },
      "male": {
        "percentage": 48,
        "index": 98
      }
    },
    "age_distribution": [
      {
        "range": "18-24",
        "percentage": 4,
        "index": 49
      },
      {
        "range": "25-34",
        "percentage": 23,
        "index": 93
      }
    ],
    "average_age": 47,
    "household_size": [
      {
        "members": "1",
        "percentage": 20,
        "index": 90
      },
      {
        "members": "2",
        "percentage": 35,
        "index": 96
      },
      {
        "members": "5+",
        "percentage": 8,
        "index": 136
      }
    ],
    "region_distribution": [
      {
        "region": "Nord Est",
        "percentage": 27,
        "index": 117
      },
      {
        "region": "Sud Est",
        "percentage": 22,
        "index": 96
      },
      {
        "region": "Nord Ouest",
        "percentage": 21,
        "index": 95
      }
    ],
    "area_of_living": [
      {
        "area": "Rural / Small town (<20,000)",
        "percentage": 51,
        "index": 95
      },
      {
        "area": "Small city / Urban (20,000–100,000)",
        "percentage": 19,
        "index": 91
      },
      {
        "area": "Metropolitan & Urban (>100,000)",
        "percentage": 30,
        "index": 117
      }
    ],
    "income_distribution": {
      "low": {
        "percentage": 13,
        "index": 68
      },
      "medium": {
        "percentage": 39,
        "index": 93
      },
      "high": {
        "percentage": 48,
        "index": 123
      },
      "average_income_eur": 3287,
      "average_income_index": 113
    },
    "education_level": [
      {
        "level": "Primary / Middle school",
        "percentage": 4,
        "index": 70
      },
      {
        "level": "High School",
        "percentage": 36,
        "index": 90
      }
    ],
    "profession_distribution": [
      {
        "role": "Junior Manager / Employee",
        "percentage": 39,
        "index": 127
      },
      {
        "role": "Retired",
        "percentage": 17,
        "index": 97
      }
    ],
    "coffee_purchase_decision": {
      "primary_decision_maker": {
        "percentage": 79,
        "index": 105
      },
      "shared_decision_maker": {
        "percentage": 21,
        "index": 83
      }
    }
  },
  "values_and_attitudes": {
    "lifestyle_statements": [
      {
        "statement": "I like to try out new food or drink products",
        "agreement_percentage": 61,
        "index": 154
      },
      {
        "statement": "When I see a new brand I often buy it to see what it's like",
        "agreement_percentage": 34,
        "index": 142
      }
    ],
    "coffee_attitudes": [
      {
        "statement": "I like to try new coffee brands",
        "agreement_percentage": 84,
        "index": 206
      },
      {
        "statement": "I like to experiment with new or lesser known coffee brands",
        "agreement_percentage": 74,
        "index": 194
      }
    ]
  },
  "sustainability_attitudes": [
    {
      "statement": "If a refill pack is available, I choose it",
      "agreement_percentage": 55,
      "index": 128
    },
    {
      "statement": "I try to buy products packaged in an environmentally friendly way",
      "agreement_percentage": 55,
      "index": 119
    }
  ],
  "coffee_consumption_traits": {
    "needstates": {
      "at_home": [
        {
          "label": "Morning Social Boost",
          "percentage": 13,
          "index": 95
        },
        {
          "label": "Morning Routine Alone",
          "percentage": 19,
          "index": 94
        }
      ],
      "out_of_home": [
        {
          "label": "On the Go Coffee Stop",
          "percentage": 4,
          "index": 71
        },
        {
          "label": "Work/School Break Alone",
          "percentage": 9,
          "index": 106
        }
      ]
    },
    "consumption_moment": {
      "at_home_only": {
        "percentage": 55,
        "index": 90
      },
      "out_of_home_only": {
        "percentage": 10,
        "index": 58
      },
      "combined": {
        "percentage": 35,
        "index": 163
      }
    },
    "time_of_consumption": {
      "at_home": [
        {
          "moment": "Before Breakfast",
          "percentage": 12,
          "index": 127
        },
        {
          "moment": "Breakfast",
          "percentage": 37,
          "index": 86
        }
      ],
      "out_of_home": [
        {
          "moment": "Before Breakfast",
          "percentage": 4,
          "index": 45
        },
        {
          "moment": "Breakfast",
          "percentage": 10,
          "index": 73
        }
      ]
    },
    "coffee_choice_motivations": [
      {
        "reason": "Has a rich taste",
        "total_segment": {
          "percentage": 35,
          "index": 150
        },
        "bean_users": {
          "percentage": 41,
          "index": 178
        }
      },
      {
        "reason": "Is easy/convenient to prepare",
        "total_segment": {
          "percentage": 33,
          "index": 95
        },
        "bean_users": {
          "percentage": 19,
          "index": 54
        }
      }
    ],
    "types_of_coffee_drinks_consumed": [
      {
        "drink": "Espresso",
        "percentage": 35,
        "index": 108
      },
      {
        "drink": "Long Black",
        "percentage": 18,
        "index": 126
      }
    ],
    "type_of_coffee_used": [
      {
        "type": "Beans",
        "percentage": 27,
        "index": 206
      },
      {
        "type": "Roast & Ground (R&G)",
        "percentage": 24,
        "index": 79
      }
    ],
    "preparation_method": [
      {
        "system": "(Super) Automatic Electric Machine (Beans)",
        "percentage": 23,
        "index": 215
      },
      {
        "system": "Filter Coffee Machine",
        "percentage": 19,
        "index": 78
      },
      {
        "system": "Electric Machine with Paper Pods",
        "percentage": 18,
        "index": 91
      },
      {
        "system": "Electric Espresso Machine with Capsules",
        "percentage": 16,
        "index": 104
      },
      {
        "system": "Electric Machine with Capsules",
        "percentage": 11,
        "index": 79
      },
      {
        "system": "Traditional Electric Machine with Group Handle (R&G)",
        "percentage": 4,
        "index": 105
      }
    ],
    "consumption_metrics": {
      "average_daily_coffees_at_home": {
        "value": 2.9,
        "index": 116
      },
      "average_daily_coffees_out_of_home": {
        "value": 2.5,
        "index": 114
      }
    },
    "coffee_grinder_usage": {
      "percentage": 3.8,
      "index": 186,
      "note": "of total segment"
    },
    "purchasing_habits": {
      "amount_spend_per_purchase": [
        {
          "bracket": "5 EUR or less",
          "percentage": 26,
          "index": 75
        },
        {
          "bracket": "6 - 10 EUR",
          "percentage": 29,
          "index": 91
        },
        {
          "bracket": "11 - 20 EUR",
          "percentage": 31,
          "index": 146
        },
        {
          "bracket": "20 EUR & above",
          "percentage": 15,
          "index": 113
        }
      ],
      "average_spend": {
        "value_eur": 14.41,
        "index": 114
      },
      "shopping_frequency": [
        {
          "frequency": "Between once every week to once every 2 weeks",
          "percentage": 49,
          "index": 124
        },
        {
          "frequency": "Between once every 2 weeks to once every month",
          "percentage": 38,
          "index": 97
        },
        {
          "frequency": "Once every month or longer",
          "percentage": 13,
          "index": 61
        }
      ],
      "average_frequency_days": {
        "value": 18.7,
        "index": 80
      }
    },
    "channel_preferences": {
      "physical_and_general": [
        {
          "channel": "Hypermarket",
          "percentage": 74,
          "index": 108
        }
      ],
      "online_breakdown": [
        {
          "site_type": "Amazon",
          "percentage": 43,
          "index": 134
        },
        {
          "site_type": "Websites specialized in selling coffee",
          "percentage": 40,
          "index": 176
        },
        {
          "site_type": "Supermarkets online stores",
          "percentage": 33,
          "index": 125
        },
        {
          "site_type": "Coffee manufacturer websites",
          "percentage": 28,
          "index": 103
        },
        {
          "site_type": "Coffee shops websites",
          "percentage": 18,
          "index": 88
        },
        {
          "site_type": "Other",
          "percentage": 10,
          "index": 116
        }
      ]
    },
    "brand_landscape": {
      "top_competitors_household_penetration": [
        {
          "brand": "Total Lavazza",
          "percentage": 5,
          "index": 126
        }
      ],
      "sub_brand_deep_dive": [
        {"lavazza": [
          {
            "sub_brand": "Lavazza Espresso",
            "percentage": 3,
            "index": 149
          },
          {
            "sub_brand": "Lavazza Il Mattino",
            "percentage": 1,
            "index": 87
          },
          {
            "sub_brand": "Lavazza Qualità Oro",
            "percentage": 0.8,
            "index": 255
          }
        ]}
      ]
    },
    "drinks_consumed": [
      {
        "drink": "Espresso (single or double shot)",
        "percentage": 39,
        "index": 110
      },
      {
        "drink": "Long black",
        "percentage": 18,
        "index": 129
      }
    ],
    "location_preferences": [
      {
        "place": "At workplace",
        "percentage": 41,
        "index": 100
      }
    ],
    "location_choice_drivers": [
      {
        "reason": "Product/brand offer",
        "percentage": 29,
        "index": 94
      }
    ],
    "preferred_bar_type": [
      {
        "type": "Basic & Traditional (A)",
        "percentage": 28,
        "index": 97
      }
    ],
    "global_coffee_chains_attitude": {
      "interest_level": {
        "interested_percentage": 56,
        "index": 120
      },
      "top_barriers_or_perceptions": [
        {
          "statement": "Don't like the coffee they serve",
          "percentage": 41,
          "index": 120
        }
      ]
    }
  },
  "brand_perception": {
    "brands": [
      {
        "brand_name": "Lavazza",
        "metrics": {
          "brand_share_percentage": 5,
          "buy_regularly_score": 22,
          "trial_score": 47,
          "awareness_score": 83
        },
        "conversion_rates": {
          "trial_to_buy_regularly": 46,
          "awareness_to_trial": 56
        },
        "sub_brand_funnels": [
          {
            "sub_brand_name": "Lavazza Espresso",
            "metrics": {
              "brand_share_percentage": 3,
              "awareness": 69,
              "trial": 35,
              "buy_regularly": 13
            },
            "conversion_rates": {
              "awareness_to_trial": 51,
              "trial_to_buy_regularly": 36
            }
          },
          {
            "sub_brand_name": "Lavazza Il Mattino",
            "metrics": {
              "brand_share_percentage": 1,
              "awareness": 35,
              "trial": 19,
              "buy_regularly": 8
            },
            "conversion_rates": {
              "awareness_to_trial": 54,
              "trial_to_buy_regularly": 42
            }
          }
        ]
      }
    ]
  },
  "machine_ownership_behavior": {
    "penetration_methods": [
      { "method": "(Super) Automatic electric espresso machine with beans", "percentage": 23, "index": 230 }
    ],
    "machine_currently_owned": [
      { "machine": "(Super) Automatic Electric Machine (Beans)", "percentage": 23, "index": 230 }
    ],
    "machine_previously_owned": [
      { "machine": "Filter Coffee Machine", "percentage": 34, "index": 102 }
    ],
    "reasons_for_switching_machineS": [
      { "reason": "To have higher quality coffee", "percentage": 47, "index": 158 }
    ],
    "capsule_machine_motivations": {
      "reasons_for_owning_machine": [
        { "reason": "I tried the coffee and I liked it", "percentage": 41, "index": 140 }
      ],
      "reasons_for_not_owning_machine": [
        { "reason": "The capsules are too expensive", "percentage": 43, "index": 104 }
      ]
    },
    "capsule_machine_brand_ownership": [
      { "brand": "Nespresso", "percentage": 48, "index": 107 }
    ],
    "machine_price_sensitivity": {
      "electric_machine_with_beans_investment": [
        { "price_bracket": "Low (<300 EUR)", "percentage": 4, "index": 28 },
        { "price_bracket": "Medium (300-399 EUR)", "percentage": 33, "index": 92 },
        { "price_bracket": "Medium high (400-499 EUR)", "percentage": 30, "index": 108 },
        { "price_bracket": "High (>500 EUR)", "percentage": 32, "index": 155 }
      ],
      "electric_machine_with_capsules_investment": [
        { "price_bracket": "Low (<70 EUR)", "percentage": 28, "index": 77 },
        { "price_bracket": "Medium (70-139 EUR)", "percentage": 46, "index": 106 },
        { "price_bracket": "Medium high (140-199 EUR)", "percentage": 20, "index": 183 },
        { "price_bracket": "High (>200 EUR)", "percentage": 2, "index": 94 }
      ]
    }
  },
  "innovation": {
    "top_concepts": [
      {
        "rank": 1,
        "concept_description": "Coffee in resealable packaging",
        "percentage": 66,
        "index": 134
      },
      {
        "rank": 2,
        "concept_description": "Coffee freshly and locally roasted",
        "percentage": 65,
        "index": 155
      }
    ]
  },
  "lifestyle": {
    "attitudes": [
      {
        "statement": "I like to try out new food products",
        "agreement_percentage": 89,
        "index_vs_coffee_drinkers": 154,
        "index_vs_all_adults": 163
      }
    ]
  },
  "sport_and_leisure": {
    "outings_and_activities": [
      { "activity": "Places of Natural Interest", "percentage": 41, "index_vs_coffee": 120, "index_vs_adults": 129 }
    ],
    "hobbies_and_interests": [
      { "hobby": "Cooking or baking", "percentage": 76, "index_vs_coffee": 141, "index_vs_adults": 167 }
    ],
    "leisure_attitudes": [
      { "statement": "I really enjoy cooking", "percentage": 82, "index_vs_coffee": 132, "index_vs_adults": 145 }
    ],
    "sports": {
      "interest_in_sports": [
        { "sport": "Football/soccer", "percentage": 45, "index_vs_coffee": 114, "index_vs_adults": 110 }
      ],
      "active_participation_sports": [
        { "sport": "Swimming", "percentage": 27, "index_vs_coffee": 140, "index_vs_adults": 146 }
      ],
      "active_participation_fitness": [
        { "activity": "Jogging/running", "percentage": 18, "index_vs_coffee": 145, "index_vs_adults": 134 }
      ]
    }
  },
  "media": {
    "media_penetration_channels": [
      {
        "channel": "Internet",
        "penetration_percentage": 100,
        "index_vs_coffee_drinkers": 101,
        "index_vs_all_adults": 101
      }
    ],
    "technology_attitudes": [
      {
        "statement": "I like to have technology that makes life easier at home",
        "agreement_percentage": 73,
        "index_vs_coffee_drinkers": 128,
        "index_vs_all_adults": 129
      }
    ],
    "channel_usage_intensity": [
      {
        "channel": "Internet",
        "usage_level": "Heavy users",
        "percentage": 19,
        "index_vs_coffee_drinkers": 133,
        "index_vs_all_adults": 127
      }
    ],
    "content_preferences": {
      "television_genres": [
        { "genre": "Sci-fi/fantasy", "percentage": 28, "index_vs_coffee_drinkers": 137, "index_vs_all_adults": 139 }
      ],
      "film_genres": [
        { "genre": "Action", "percentage": 18, "index_vs_coffee_drinkers": 140, "index_vs_all_adults": 128 }
      ],
      "podcast_genres": [
        { "genre": "On-demand programmes", "percentage": 20, "index_vs_coffee_drinkers": 125, "index_vs_all_adults": 128 }
      ],
      "radio_programmes": [
        { "genre": "Generalist radio stations – Mornings", "percentage": 44, "index_vs_coffee_drinkers": 120, "index_vs_all_adults": 129 }
      ],
      "newspaper_topics": [
        { "topic": "National news", "percentage": 36, "index_vs_coffee_drinkers": 152, "index_vs_all_adults": 171 }
      ]
    },
    "internet_consumption_profile": {
    "social_media_behavior": {
      "time_spent_frequency": [
        { "frequency": "More than 10 times a day", "percentage": 15, "vs_coffee_drinkers": "Higher" }
      ],
      "brands_used": [
        { "platform": "YouTube", "penetration": 59, "index_vs_coffee": 127, "index_vs_adults": 124 }
      ]
    },
    "online_research_topics": [
      { "topic": "The environment", "percentage": 25, "description": "compare vs 18% Total Coffee Drinkers" }
    ],
    "device_usage": [
      { "device": "Tablet", "penetration": 36, "index_vs_coffee": 123, "index_vs_adults": 133 }
    ],
    "website_visitation_last_4_weeks": [
      { "site": "YouTube", "penetration": 53, "index_vs_coffee": 126, "index_vs_adults": 127 }
    ],
    "online_activities_daily": [
      { "activity": "Make internet or video calls", "penetration": 16, "index_vs_coffee": 140 }
    ]
  }
  }
}
```


## **1. Top-level fields**

| Field                        | Type          | Description                                              |
| ---------------------------- | ------------- | -------------------------------------------------------- |
| `persona_id`                 | string        | Unique identifier of the persona.                        |
| `segment_name`               | string        | Human-readable persona name.                             |
| `locale`                     | string        | Locale code following ISO (`fr_FR`).                     |
| `source_reference`           | object        | Source metadata for traceability.                        |
| `core_profile_overview`      | object        | High-level persona summary.                              |
| `demographics`               | object        | Structured demographic fields.                           |
| `values_and_attitudes`       | object        | General lifestyle + coffee-specific attitude statements. |
| `sustainability_attitudes`   | array<object> | Sustainability statements with metrics.                  |
| `coffee_consumption_traits`  | object        | All metrics linked to coffee usage.                      |
| `brand_perception`           | object        | Brand funnel metrics and perception data.                |
| `machine_ownership_behavior` | object        | Ownership and usage of coffee machines.                  |
| `innovation`                 | object        | Innovation concept ranking and interest.                 |
| `lifestyle`                  | object        | Extended lifestyle attitudes.                            |
| `sport_and_leisure`          | object        | Leisure, hobbies, and sports data.                       |
| `media`                      | object        | Media usage, content preferences, and digital behaviour. |

---

## **2. `source_reference`**

| Field              | Type       | Description                          |
| ------------------ | ---------- | ------------------------------------ |
| `document`         | string     | Exact source document name.          |
| `pages`            | array<int> | Pages where data was extracted from. |
| `extraction_notes` | string     | Additional context or manual notes.  |

---

## **3. `core_profile_overview`**

#### **3.1 `market_impact`**

| Field                         | Type   | Description                                 |
| ----------------------------- | ------ | ------------------------------------------- |
| `population_share_percentage` | number | Persona share of total population.          |
| `value_share_percentage`      | number | Persona share of category market value.     |
| `spend_at_home_index`         | number | Indexed spending level vs total population. |

#### **3.2 `identity_summary`**

| Field            | Type   | Description                                       |
| ---------------- | ------ | ------------------------------------------------- |
| `demographics`   | string | Plain-text demographic summary.                   |
| `psychographics` | string | Plain-text psychographic and behavioural summary. |

#### **3.3 `sustainability_attitude`**

| Field       | Type   | Description                         |
| ----------- | ------ | ----------------------------------- |
| `statement` | string | Core sustainability-related belief. |
| `index`     | number | Index vs national population.       |

#### **3.4 `consumption_habits`**

##### **At home (`at_home`)**

| Field                          | Type   | Description                       |
| ------------------------------ | ------ | --------------------------------- |
| `volume.average_daily_coffees` | number | Daily consumption volume at home. |
| `volume.index`                 | number | Indexed vs national average.      |
| `behavior_description`         | string | Qualitative consumption summary.  |

##### **Out of home (`out_of_home`)**

Same structure as above.

#### **3.5 `shopping_attitude`**

| Field       | Type   | Description                                |
| ----------- | ------ | ------------------------------------------ |
| `statement` | string | Attitude toward coffee shopping behaviour. |
| `index`     | number | Index vs national population.              |

#### **3.6 `innovation_interest`**

| Field     | Type   | Description                                     |
| --------- | ------ | ----------------------------------------------- |
| `summary` | string | High-level statement about innovation affinity. |

---

## **4. `demographics`**

#### **4.1 `gender_distribution`**

| Field               | Type   | Description                         |
| ------------------- | ------ | ----------------------------------- |
| `female.percentage` | number | % of persona identifying as female. |
| `female.index`      | number | Index vs total population.          |
| `male.percentage`   | number | % male.                             |
| `male.index`        | number | Index vs total population.          |

#### **4.2 `age_distribution`**

Array of:

| Field        | Type   | Description                    |
| ------------ | ------ | ------------------------------ |
| `range`      | string | Age bracket (e.g., `"35-44"`). |
| `percentage` | number | % of persona.                  |
| `index`      | number | Index vs national population.  |

#### **4.3 Other demographic fields**

| Field                      | Type          | Description                             |
| -------------------------- | ------------- | --------------------------------------- |
| `average_age`              | number        | Mean age.                               |
| `household_size`           | array<object> | Members per household bracket.          |
| `region_distribution`      | array<object> | Regional share + index.                 |
| `area_of_living`           | array<object> | Rural/urban distribution.               |
| `income_distribution`      | object        | Income brackets, averages, and indexes. |
| `education_level`          | array<object> | Distribution by highest education.      |
| `profession_distribution`  | array<object> | Distribution across job categories.     |
| `coffee_purchase_decision` | object        | Primary vs shared decision maker.       |

---

## **5. `values_and_attitudes`**

#### **5.1 `lifestyle_statements`**

Each entry:

| Field                  | Type   | Description                    |
| ---------------------- | ------ | ------------------------------ |
| `statement`            | string | Lifestyle-related belief.      |
| `agreement_percentage` | number | % agreeing with the statement. |
| `index`                | number | Index vs national population.  |

#### **5.2 `coffee_attitudes`**

Same structure but focused on coffee-specific behaviours.

---

## **6. `sustainability_attitudes`**

Array of:

| Field                  | Type   | Description                    |
| ---------------------- | ------ | ------------------------------ |
| `statement`            | string | Sustainability-related belief. |
| `agreement_percentage` | number | % of persona who agrees.       |
| `index`                | number | Indexed vs population.         |

---

## **7. `coffee_consumption_traits`**

A detailed hierarchical block containing all behavioural KPIs.

---

### **7.1 `needstates`**

#### **At home (`at_home`)**

List of needstate objects.

| Field        | Type   | Description                   |
| ------------ | ------ | ----------------------------- |
| `label`      | string | Needstate name.               |
| `percentage` | number | % of respondents.             |
| `index`      | number | Index vs national population. |

#### **Out of home (`out_of_home`)**

Same structure.

---

### **7.2 `consumption_moment`**

| Field              | Type   | Description                                 |
| ------------------ | ------ | ------------------------------------------- |
| `at_home_only`     | object | Percentage + index for home-only consumers. |
| `out_of_home_only` | object | Same for OOH-only.                          |
| `combined`         | object | Consumers engaging in both.                 |

---

### **7.3 `time_of_consumption`**

Two arrays:

* `at_home`
* `out_of_home`

Each record:

| Field        | Type   | Description                    |
| ------------ | ------ | ------------------------------ |
| `moment`     | string | Daypart (e.g., `"Breakfast"`). |
| `percentage` | number | Share of consumption.          |
| `index`      | number | Index vs population.           |

---

### **7.4 `coffee_choice_motivations`**

Each record:

| Field                      | Type   | Description                           |
| -------------------------- | ------ | ------------------------------------- |
| `reason`                   | string | Motivation for choosing coffee type.  |
| `total_segment.percentage` | number | % of total persona mentioning reason. |
| `total_segment.index`      | number | Index vs population average.          |
| `bean_users.percentage`    | number | % of bean users mentioning reason.    |
| `bean_users.index`         | number | Index vs bean-user average.           |

---

### **7.5 Coffee Usage & Format Fields**

#### **`types_of_coffee_drinks_consumed`**

Array of:

* `drink`
* `percentage`
* `index`

#### **`type_of_coffee_used`**

Array of:

* `type`
* `percentage`
* `index`

#### **`preparation_method`**

Array of:

* `system`
* `percentage`
* `index`

#### **`consumption_metrics`**

| Field                                     | Type   | Description         |
| ----------------------------------------- | ------ | ------------------- |
| `average_daily_coffees_at_home.value`     | number | Cups per day (AH).  |
| `average_daily_coffees_at_home.index`     | number | Index vs norm.      |
| `average_daily_coffees_out_of_home.value` | number | Cups per day (OOH). |
| `average_daily_coffees_out_of_home.index` | number | Index vs norm.      |

#### **`coffee_grinder_usage`**

| Field        | Type   | Description               |
| ------------ | ------ | ------------------------- |
| `percentage` | number | Grinder user share.       |
| `index`      | number | Index vs population.      |
| `note`       | string | Optional additional note. |

---

### **7.6 `purchasing_habits`**

Contains:

* **`amount_spend_per_purchase`**: price tier distribution
* **`average_spend`**: numeric value + index
* **`shopping_frequency`**: frequency brackets
* **`average_frequency_days`**: mean purchase interval

---

### **7.7 `channel_preferences`**

Two sections:

#### **Physical + general channels (`physical_and_general`)**

* `channel`
* `percentage`
* `index`

#### **Online breakdown (`online_breakdown`)**

* `site_type`
* `percentage`
* `index`

---

### **7.8 `brand_landscape`**

#### **`top_competitors_household_penetration`**

Array of brand entries.

| Field        | Type   | Description            |
| ------------ | ------ | ---------------------- |
| `brand`      | string | Brand name.            |
| `percentage` | number | Household penetration. |
| `index`      | number | Index vs population.   |

#### **`sub_brand_deep_dive`**

Array of brand-keyed objects. Each object uses the brand name as key, and the value is an
array of sub-brand entries:

* `sub_brand`
* `percentage`
* `index`

---

### **7.9 Location & Venue Behaviour**

#### **`location_preferences`**

OOH consumption locations.

#### **`location_choice_drivers`**

Reasons for choosing a given place.

#### **`preferred_bar_type`**

Preference across A/B/C/D bar formats.

#### **`global_coffee_chains_attitude`**

Interest + barriers.

---

## **8. `brand_perception`**

#### **Per-Brand Metrics**

Each brand:

* `brand_name`
* `brand_share_percentage`
* `metrics.buy_regularly_score`
* `metrics.trial_score`
* `metrics.awareness_score`
* `conversion_rates.trial_to_buy_regularly`
* `conversion_rates.awareness_to_trial`

#### **Sub-brand funnels**

If available:

* awareness
* trial
* buy regularly
* conversion rates

---

## **9. `machine_ownership_behavior`**

#### **`penetration_methods`**

Ownership penetration per machine type.

#### **`machine_currently_owned`**

Most-used machines.

#### **`machine_previously_owned`**

Legacy machines.

#### **`reasons_for_switching_machineS`**

Drivers of machine switching.

#### **Capsule Machine Motivations**

* Reasons for owning
* Reasons for not owning

#### **Capsule Machine Brand Ownership**

Brand-level ownership shares.

#### **Price Sensitivity**

Two structures:

* bean machines (`electric_machine_with_beans_investment`)
* capsule machines (`electric_machine_with_capsules_investment`)

---

## **10. `innovation`**

| Field          | Type  | Description                              |
| -------------- | ----- | ---------------------------------------- |
| `top_concepts` | array | Concept ranking with percentage + index. |

---

## **11. `lifestyle`**

Contains:

#### **`attitudes`**

Array:

* `statement`
* `agreement_percentage`
* `index_vs_coffee_drinkers`
* `index_vs_all_adults`

---

## **12. `sport_and_leisure`**

Includes:

* `outings_and_activities`
* `hobbies_and_interests`
* `leisure_attitudes`
* `sports.interest_in_sports`
* `sports.active_participation_sports`
* `sports.active_participation_fitness`

All with percentage + indexes.

---

## **13. `media`**

Includes several structured components:

#### **`media_penetration_channels`**

Penetration + index vs two baselines.

#### **`technology_attitudes`**

Tech-related statements.

#### **`channel_usage_intensity`**

Heavy/medium usage for each channel.

#### **`content_preferences`**

TV genres, film genres, podcasts, radio, newspaper.

#### **`internet_consumption_profile`**

Contains:

* `social_media_behavior`
* `online_research_topics`
* `device_usage`
* `website_visitation_last_4_weeks`
* `online_activities_daily`

Each with penetration + indexes where applicable.
