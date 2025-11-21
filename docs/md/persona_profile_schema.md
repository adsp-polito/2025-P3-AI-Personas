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
      },
      {
        "range": "35-44",
        "percentage": 15,
        "index": 98
      },
      {
        "range": "45-54",
        "percentage": 24,
        "index": 114
      },
      {
        "range": "55-70",
        "percentage": 35,
        "index": 110
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
        "members": "3",
        "percentage": 20,
        "index": 101
      },
      {
        "members": "4",
        "percentage": 17,
        "index": 107
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
      },
      {
        "region": "Ile de France",
        "percentage": 18,
        "index": 91
      },
      {
        "region": "Sud Ouest",
        "percentage": 11,
        "index": 97
      },
      {
        "region": "Corsica",
        "percentage": 1,
        "index": 204
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
      "average_income_index": 113,
      "income_brackets": [
        {
          "range": "≤1500",
          "percentage": 5,
          "index": 66
        },
        {
          "range": "1501–3000",
          "percentage": 2,
          "index": 54
        },
        {
          "range": "1501–3000",
          "percentage": 6,
          "index": 79
        },
        {
          "range": "3001+",
          "percentage": 9,
          "index": 65
        },
        {
          "range": "1501–3000",
          "percentage": 15,
          "index": 106
        },
        {
          "range": "3001+",
          "percentage": 15,
          "index": 107
        },
        {
          "range": "3001+",
          "percentage": 28,
          "index": 110
        },
        {
          "range": "3001+",
          "percentage": 15,
          "index": 149
        },
        {
          "range": "3001+",
          "percentage": 5,
          "index": 142
        }
      ]
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
      },
      {
        "level": "BA Degree",
        "percentage": 38,
        "index": 107
      },
      {
        "level": "MA Degree",
        "percentage": 19,
        "index": 120
      },
      {
        "level": "Post-doctorate",
        "percentage": 3,
        "index": 108
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
      },
      {
        "role": "Director / Manager",
        "percentage": 6,
        "index": 109
      },
      {
        "role": "Factory / Farm Worker",
        "percentage": 6,
        "index": 71
      },
      {
        "role": "Self-employed",
        "percentage": 5,
        "index": 128
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
      },
      {
        "statement": "It's worth paying extra for quality goods",
        "agreement_percentage": 62,
        "index": 136
      },
      {
        "statement": "I often read food labels to see the list of ingredients",
        "agreement_percentage": 56,
        "index": 127
      },
      {
        "statement": "I like to pursue a life of challenge, novelty and change",
        "agreement_percentage": 36,
        "index": 125
      },
      {
        "statement": "I consider myself to be a creative person",
        "agreement_percentage": 45,
        "index": 124
      },
      {
        "statement": "I am prepared to pay more for products that make life easier",
        "agreement_percentage": 42,
        "index": 119
      },
      {
        "statement": "I check a number of sources before making a significant purchase",
        "agreement_percentage": 63,
        "index": 118
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
      },
      {
        "statement": "I like to discover new coffee types (e.g. ready-to-drink iced coffee, cold brew coffee, espresso coffee) or flavors",
        "agreement_percentage": 83,
        "index": 183
      },
      {
        "statement": "The origin of the beans plays a big role in my decision for a coffee",
        "agreement_percentage": 86,
        "index": 179
      },
      {
        "statement": "I like to buy different types of coffee to serve to guests",
        "agreement_percentage": 82,
        "index": 167
      },
      {
        "statement": "I like to be inspired about new types and brands of coffee when drinking coffee outside of home",
        "agreement_percentage": 75,
        "index": 163
      },
      {
        "statement": "I enjoy feeling like a barista or an expert while making coffee in a sophisticated way",
        "agreement_percentage": 40,
        "index": 154
      },
      {
        "statement": "I enjoy using coffee beans to get a better coffee quality",
        "agreement_percentage": 75,
        "index": 154
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
    },
    {
      "statement": "I try to buy products with packaging made from recycled materials",
      "agreement_percentage": 51,
      "index": 116
    },
    {
      "statement": "It is difficult to be more environmentally friendly because the products that are better for the environment are harder to find or more expensive",
      "agreement_percentage": 49,
      "index": 102
    },
    {
      "statement": "I try to buy from companies whose workers are not discriminated against",
      "agreement_percentage": 47,
      "index": 117
    },
    {
      "statement": "I see friends and family changing their behaviours to be more environmentally friendly",
      "agreement_percentage": 46,
      "index": 115
    },
    {
      "statement": "When I drink hot drinks on the go, I use a reusable (to go) cup",
      "agreement_percentage": 42,
      "index": 118
    },
    {
      "statement": "I feel that I can make a difference to the world around me through the choices I make and the actions I take",
      "agreement_percentage": 41,
      "index": 113
    },
    {
      "statement": "Buying sustainable products shows others who I am and what I believe in",
      "agreement_percentage": 36,
      "index": 107
    },
    {
      "statement": "I deliberately avoid buying drinks in plastic bottles",
      "agreement_percentage": 32,
      "index": 103
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
        },
        {
          "label": "Fresh Morning Start",
          "percentage": 11,
          "index": 124
        },
        {
          "label": "Lunch Together at Home",
          "percentage": 13,
          "index": 118
        },
        {
          "label": "Afternoon Break with Family",
          "percentage": 5,
          "index": 78
        },
        {
          "label": "Afternoon Reward at Home",
          "percentage": 14,
          "index": 124
        },
        {
          "label": "After Dinner Unwind",
          "percentage": 6,
          "index": 106
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
        },
        {
          "label": "Work/School Afternoon Bonding",
          "percentage": 3,
          "index": 55
        },
        {
          "label": "Indulgent Break with Friends",
          "percentage": 3,
          "index": 91
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
        },
        {
          "moment": "Mid-morning",
          "percentage": 11,
          "index": 99
        },
        {
          "moment": "Lunch",
          "percentage": 16,
          "index": 108
        },
        {
          "moment": "Mid-afternoon",
          "percentage": 18,
          "index": 111
        },
        {
          "moment": "Dinner",
          "percentage": 3,
          "index": 159
        },
        {
          "moment": "After-dinner",
          "percentage": 4,
          "index": 92
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
        },
        {
          "moment": "Mid-morning",
          "percentage": 30,
          "index": 108
        },
        {
          "moment": "Lunch",
          "percentage": 24,
          "index": 115
        },
        {
          "moment": "Mid-afternoon",
          "percentage": 30,
          "index": 120
        },
        {
          "moment": "Dinner",
          "percentage": 1,
          "index": 52
        },
        {
          "moment": "After-dinner",
          "percentage": 2,
          "index": 60
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
      },
      {
        "reason": "Has high quality coffee",
        "total_segment": {
          "percentage": 30,
          "index": 167
        },
        "bean_users": {
          "percentage": 44,
          "index": 249
        }
      },
      {
        "reason": "Has a strong taste",
        "total_segment": {
          "percentage": 26,
          "index": 149
        },
        "bean_users": {
          "percentage": 24,
          "index": 140
        }
      },
      {
        "reason": "Can be made just how you like it",
        "total_segment": {
          "percentage": 24,
          "index": 117
        },
        "bean_users": {
          "percentage": 21,
          "index": 103
        }
      },
      {
        "reason": "Is high in caffeine content",
        "total_segment": {
          "percentage": 18,
          "index": 140
        },
        "bean_users": {
          "percentage": 18,
          "index": 140
        }
      },
      {
        "reason": "Is affordable / has the right price",
        "total_segment": {
          "percentage": 17,
          "index": 82
        },
        "bean_users": {
          "percentage": 15,
          "index": 70
        }
      },
      {
        "reason": "Has a light, mild taste",
        "total_segment": {
          "percentage": 16,
          "index": 97
        },
        "bean_users": {
          "percentage": 8,
          "index": 50
        }
      },
      {
        "reason": "Is a source of healthy energy",
        "total_segment": {
          "percentage": 15,
          "index": 132
        },
        "bean_users": {
          "percentage": 21,
          "index": 189
        }
      },
      {
        "reason": "Is completely natural",
        "total_segment": {
          "percentage": 12,
          "index": 144
        },
        "bean_users": {
          "percentage": 15,
          "index": 171
        }
      }
    ],
    "types_of_coffee_drinks_consumedS": [
      {
        "drink": "Espresso",
        "percentage": 35,
        "index": 108
      },
      {
        "drink": "Long Black",
        "percentage": 18,
        "index": 126
      },
      {
        "drink": "Filter Coffee",
        "percentage": 16,
        "index": 79
      },
      {
        "drink": "Flat White",
        "percentage": 9,
        "index": 80
      },
      {
        "drink": "Cappuccino",
        "percentage": 6,
        "index": 128
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
      },
      {
        "type": "Capsules (NCC)",
        "percentage": 16,
        "index": 104
      },
      {
        "type": "Capsules (CS)",
        "percentage": 11,
        "index": 79
      },
      {
        "type": "Paper pods",
        "percentage": 18,
        "index": 91
      },
      {
        "type": "Instant",
        "percentage": 3,
        "index": 49
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
        },
        {
          "channel": "Supermarket",
          "percentage": 28,
          "index": 98
        },
        {
          "channel": "Roaster / Local roaster",
          "percentage": 14,
          "index": 274
        },
        {
          "channel": "Official retailer of my favorite brand",
          "percentage": 14,
          "index": 161
        },
        {
          "channel": "Via web (e-commerce) / online",
          "percentage": 10,
          "index": 131
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
        },
        {
          "brand": "Total Carte Noire",
          "percentage": 14,
          "index": 122
        },
        {
          "brand": "L'Or",
          "percentage": 10,
          "index": 108
        },
        {
          "brand": "Senseo",
          "percentage": 10,
          "index": 80
        },
        {
          "brand": "Nespresso",
          "percentage": 8,
          "index": 104
        },
        {
          "brand": "Nescafé Dolce Gusto",
          "percentage": 6,
          "index": 89
        },
        {
          "brand": "Private Label",
          "percentage": 5,
          "index": 80
        },
        {
          "brand": "Méo",
          "percentage": 4,
          "index": 205
        },
        {
          "brand": "Starbucks",
          "percentage": 3,
          "index": 136
        },
        {
          "brand": "Café Royal",
          "percentage": 2,
          "index": 208
        },
        {
          "brand": "Illy",
          "percentage": 1,
          "index": 165
        }
      ],
      "sub_brand_deep_dive": {
        "lavazza": [
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
        ],
        "carte_noire": [
          {
            "sub_brand": "Carte Noire (Core)",
            "percentage": 8,
            "index": 92
          },
          {
            "sub_brand": "Carte Noire Bio",
            "percentage": 3,
            "index": 162
          },
          {
            "sub_brand": "Carte Noire Secrets de Nature",
            "percentage": 2,
            "index": 364
          },
          {
            "sub_brand": "Carte Noire Douceur Intense",
            "percentage": 1,
            "index": 187
          },
          {
            "sub_brand": "Carte Noire Torrefacteur",
            "percentage": 1,
            "index": 351
          }
        ]
      }
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
      },
      {
        "drink": "Ristretto",
        "percentage": 11,
        "index": 239
      },
      {
        "drink": "Cappuccino",
        "percentage": 10,
        "index": 112
      },
      {
        "drink": "Filter coffee",
        "percentage": 5,
        "index": 57
      }
    ],
    "location_preferences": [
      {
        "place": "At workplace",
        "percentage": 41,
        "index": 100
      },
      {
        "place": "An independent coffee shop /bar/ café",
        "percentage": 11,
        "index": 156
      },
      {
        "place": "At a coffee chain shop / bar/ café",
        "percentage": 8,
        "index": 131
      },
      {
        "place": "At a takeaway restaurant",
        "percentage": 6,
        "index": 220
      },
      {
        "place": "At hospital / public offices",
        "percentage": 5,
        "index": 176
      },
      {
        "place": "At a pizzeria / pizza chain",
        "percentage": 5,
        "index": 115
      },
      {
        "place": "At a brasserie",
        "percentage": 5,
        "index": 99
      }
    ],
    "location_choice_drivers": [
      {
        "reason": "Product/brand offer",
        "percentage": 29,
        "index": 94
      },
      {
        "reason": "Environment/services/facilities",
        "percentage": 27,
        "index": 104
      },
      {
        "reason": "Convenience",
        "percentage": 24,
        "index": 92
      },
      {
        "reason": "Quality",
        "percentage": 11,
        "index": 152
      },
      {
        "reason": "Price",
        "percentage": 10,
        "index": 92
      }
    ],
    "preferred_bar_type": [
      {
        "type": "Basic & Traditional (A)",
        "percentage": 28,
        "index": 97
      },
      {
        "type": "Classic Local (B)",
        "percentage": 36,
        "index": 119
      },
      {
        "type": "Social Mood Shift (C)",
        "percentage": 13,
        "index": 54
      },
      {
        "type": "Specialty & Trendy (D)",
        "percentage": 23,
        "index": 135
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
        },
        {
          "statement": "Not interested in such places",
          "percentage": 40,
          "index": 96
        },
        {
          "statement": "They are too commercial",
          "percentage": 30,
          "index": 140
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
      },
      {
        "brand_name": "Carte Noire",
        "brand_share_percentage": 14,
        "metrics": {
          "buy_regularly_score": 32,
          "trial_score": 63,
          "awareness_score": 89
        },
        "conversion_rates": {
          "trial_to_buy_regularly": 51,
          "awareness_to_trial": 71
        }
      },
      {
        "brand_name": "L'Or",
        "brand_share_percentage": 10,
        "metrics": {
          "buy_regularly_score": 31,
          "trial_score": 62,
          "awareness_score": 91
        },
        "conversion_rates": {
          "trial_to_buy_regularly": 49,
          "awareness_to_trial": 69
        }
      },
      {
        "brand_name": "Senseo",
        "brand_share_percentage": 10,
        "metrics": {
          "buy_regularly_score": 16,
          "trial_score": 48,
          "awareness_score": 88
        },
        "conversion_rates": {
          "trial_to_buy_regularly": 34,
          "awareness_to_trial": 54
        }
      },
      {
        "brand_name": "Nespresso",
        "brand_share_percentage": 8,
        "metrics": {
          "buy_regularly_score": 14,
          "trial_score": 46,
          "awareness_score": 89
        },
        "conversion_rates": {
          "trial_to_buy_regularly": 30,
          "awareness_to_trial": 52
        }
      },
      {
        "brand_name": "Nescafé Dolce Gusto",
        "brand_share_percentage": 6,
        "metrics": {
          "buy_regularly_score": 12,
          "trial_score": 39,
          "awareness_score": 83
        },
        "conversion_rates": {
          "trial_to_buy_regularly": 31,
          "awareness_to_trial": 47
        }
      },
      {
        "brand_name": "Private Label",
        "brand_share_percentage": 5,
        "metrics": {
          "buy_regularly_score": 9,
          "trial_score": 25,
          "awareness_score": 48
        },
        "conversion_rates": {
          "trial_to_buy_regularly": 33,
          "awareness_to_trial": 52
        }
      },
      {
        "brand_name": "Méo",
        "brand_share_percentage": 4,
        "metrics": {
          "buy_regularly_score": 6,
          "trial_score": 20,
          "awareness_score": 45
        },
        "conversion_rates": {
          "trial_to_buy_regularly": 28,
          "awareness_to_trial": 44
        }
      },
      {
        "brand_name": "Starbucks Coffee",
        "brand_share_percentage": 3,
        "metrics": {
          "buy_regularly_score": 12,
          "trial_score": 41,
          "awareness_score": 77
        },
        "conversion_rates": {
          "trial_to_buy_regularly": 30,
          "awareness_to_trial": 53
        }
      }
    ]
  },
  "machine_ownership_behavior": {
    "penetration_methods": [
      { "method": "(Super) Automatic electric espresso machine with beans", "percentage": 23, "index": 230 },
      { "method": "Electric Nespresso machine with capsules", "percentage": 19, "index": 115 },
      { "method": "Electric machine with paper pods", "percentage": 16, "index": 79 },
      { "method": "Filter coffee machine", "percentage": 16, "index": 71 },
      { "method": "Electric Dolce Gusto / Tassimo machine with capsules", "percentage": 14, "index": 91 },
      { "method": "Traditional electric espresso machine with group handle", "percentage": 5, "index": 123 },
      { "method": "Instant coffee", "percentage": 2, "index": 40 },
      { "method": "A moka pot (classic or electric)", "percentage": 2, "index": 66 },
      { "method": "Cafetiere / plunger (French press)", "percentage": 2, "index": 107 }
    ],
    "machine_currently_owned": [
      { "machine": "(Super) Automatic Electric Machine (Beans)", "percentage": 23, "index": 230 },
      { "machine": "Electric Nespresso Machine with Capsules", "percentage": 19, "index": 115 },
      { "machine": "Electric Machine with Paper Pods", "percentage": 16, "index": 79 }
    ],
    "machine_previously_owned": [
      { "machine": "Filter Coffee Machine", "percentage": 34, "index": 102 },
      { "machine": "Electric Machine with Paper Pods", "percentage": 18, "index": 94 },
      { "machine": "Electric Nespresso Machine with Capsules", "percentage": 16, "index": 142 }
    ],
    "reasons_for_switching_machineS": [
      { "reason": "To have higher quality coffee", "percentage": 47, "index": 158 },
      { "reason": "I tried the coffee and I liked its flavor", "percentage": 41, "index": 143 },
      { "reason": "To make coffee in a more convenient way", "percentage": 26, "index": 96 },
      { "reason": "It allows me to make the coffee in my own way", "percentage": 25, "index": 137 },
      { "reason": "To have wider selection of coffee types", "percentage": 24, "index": 139 },
      { "reason": "More environmental friendly option to make coffee", "percentage": 16, "index": 149 },
      { "reason": "It was a gift", "percentage": 16, "index": 86 },
      { "reason": "It's a more affordable way to make coffee", "percentage": 14, "index": 90 }
    ],
    "capsule_machine_motivations": {
      "reasons_for_owning_machine": [
        { "reason": "I tried the coffee and I liked it", "percentage": 41, "index": 140 },
        { "reason": "For practical preparation, it is easy to use", "percentage": 33, "index": 111 },
        { "reason": "It has a wide variety of capsules / flavors / variants in its range", "percentage": 31, "index": 133 },
        { "reason": "It has a wide selection of compatible capsules in its range", "percentage": 31, "index": 126 },
        { "reason": "I trust the brand", "percentage": 29, "index": 104 }
      ],
      "reasons_for_not_owning_machine": [
        { "reason": "The capsules are too expensive", "percentage": 43, "index": 104 },
        { "reason": "For the environmental impact of the capsules", "percentage": 34, "index": 162 },
        { "reason": "I like coffee in my own way", "percentage": 29, "index": 117 },
        { "reason": "The machine is too expensive", "percentage": 15, "index": 64 },
        { "reason": "I don't like it", "percentage": 15, "index": 130 }
      ]
    },
    "capsule_machine_brand_ownership": [
      { "brand": "Nespresso", "percentage": 48, "index": 107 },
      { "brand": "Nescafe Dolce Gusto", "percentage": 38, "index": 122 },
      { "brand": "Tassimo", "percentage": 20, "index": 93 }
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
      },
      {
        "rank": 3,
        "concept_description": "Coffee in sustainable packaging",
        "percentage": 61,
        "index": 129
      },
      {
        "rank": 4,
        "concept_description": "Coffee produced from different variety of beans other than Arabica and Robusta",
        "percentage": 56,
        "index": 156
      },
      {
        "rank": 5,
        "concept_description": "Coffee capsules that are fully compostable",
        "percentage": 54,
        "index": 115
      },
      {
        "rank": 6,
        "concept_description": "Coffee that is gentle with stomach & assists digestive health",
        "percentage": 51,
        "index": 116
      },
      {
        "rank": 7,
        "concept_description": "Organic coffee",
        "percentage": 50,
        "index": 135
      },
      {
        "rank": 8,
        "concept_description": "Coffee in bulk that is eco-friendly thanks to the absence of packaging (i.e. you bring your own container and fill it with coffee in store)",
        "percentage": 49,
        "index": 137
      },
      {
        "rank": 9,
        "concept_description": "Customized espresso blend (i.e. pack, type of roasting, blend profile) according to your taste guided by our master-blenders suggestions",
        "percentage": 48,
        "index": 153
      },
      {
        "rank": 10,
        "concept_description": "Coffee ground perfectly for specific brewing method (e.g. French press, Espresso, drip coffee)",
        "percentage": 46,
        "index": 130
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
      },
      {
        "statement": "I enjoy eating foreign food",
        "agreement_percentage": 87,
        "index_vs_coffee_drinkers": 132,
        "index_vs_all_adults": 138
      },
      {
        "statement": "I am very worried about the consequences of climate change",
        "agreement_percentage": 82,
        "index_vs_coffee_drinkers": 120,
        "index_vs_all_adults": 123
      },
      {
        "statement": "I am willing to spend more on good quality foods",
        "agreement_percentage": 82,
        "index_vs_coffee_drinkers": 136,
        "index_vs_all_adults": 143
      },
      {
        "statement": "Brands should play a major role in the fight against all forms of discrimination",
        "agreement_percentage": 79,
        "index_vs_coffee_drinkers": 120,
        "index_vs_all_adults": 124
      },
      {
        "statement": "Children should be allowed to express themselves freely",
        "agreement_percentage": 73,
        "index_vs_coffee_drinkers": 120,
        "index_vs_all_adults": 121
      },
      {
        "statement": "I am worried about pollution and congestion caused by cars",
        "agreement_percentage": 72,
        "index_vs_coffee_drinkers": 126,
        "index_vs_all_adults": 132
      },
      {
        "statement": "I am prepared to make lifestyle compromises to benefit the environment",
        "agreement_percentage": 72,
        "index_vs_coffee_drinkers": 128,
        "index_vs_all_adults": 131
      },
      {
        "statement": "I like to be surrounded by different people, cultures, ideas and lifestyles",
        "agreement_percentage": 70,
        "index_vs_coffee_drinkers": 127,
        "index_vs_all_adults": 129
      },
      {
        "statement": "I take great pleasure in looking after my appearance",
        "agreement_percentage": 70,
        "index_vs_coffee_drinkers": 127,
        "index_vs_all_adults": 132
      },
      {
        "statement": "My fragrance expresses my personality",
        "agreement_percentage": 69,
        "index_vs_coffee_drinkers": 137,
        "index_vs_all_adults": 145
      },
      {
        "statement": "I am eating more healthy food than I have in the past",
        "agreement_percentage": 68,
        "index_vs_coffee_drinkers": 122,
        "index_vs_all_adults": 129
      },
      {
        "statement": "I like to try new recipes",
        "agreement_percentage": 68,
        "index_vs_coffee_drinkers": 159,
        "index_vs_all_adults": 171
      },
      {
        "statement": "I am an optimist",
        "agreement_percentage": 68,
        "index_vs_coffee_drinkers": 124,
        "index_vs_all_adults": 127
      },
      {
        "statement": "We usually have family meals at the Weekend",
        "agreement_percentage": 68,
        "index_vs_coffee_drinkers": 127,
        "index_vs_all_adults": 129
      },
      {
        "statement": "I am a perfectionist",
        "agreement_percentage": 67,
        "index_vs_coffee_drinkers": 121,
        "index_vs_all_adults": 123
      }
    ]
  },
  "sport_and_leisure": {
    "outings_and_activities": [
      { "activity": "Places of Natural Interest", "percentage": 41, "index_vs_coffee": 120, "index_vs_adults": 129 },
      { "activity": "Fairground", "percentage": 37, "index_vs_coffee": 124, "index_vs_adults": 124 },
      { "activity": "Music Festivals", "percentage": 29, "index_vs_coffee": 137, "index_vs_adults": 145 },
      { "activity": "Nature reserves and other nature related places", "percentage": 28, "index_vs_coffee": 123, "index_vs_adults": 133 },
      { "activity": "Pubs, theme bars", "percentage": 25, "index_vs_coffee": 147, "index_vs_adults": 143 },
      { "activity": "Louvre", "percentage": 23, "index_vs_coffee": 124, "index_vs_adults": 125 },
      { "activity": "Eiffel Tower", "percentage": 22, "index_vs_coffee": 127, "index_vs_adults": 125 },
      { "activity": "Exhibitions, art galleries", "percentage": 19, "index_vs_coffee": 123, "index_vs_adults": 128 },
      { "activity": "Chateau de Versailles", "percentage": 19, "index_vs_coffee": 121, "index_vs_adults": 123 },
      { "activity": "Theme Parks/Water Parks", "percentage": 19, "index_vs_coffee": 137, "index_vs_adults": 129 }
    ],
    "hobbies_and_interests": [
      { "hobby": "Cooking or baking", "percentage": 76, "index_vs_coffee": 141, "index_vs_adults": 167 },
      { "hobby": "Gardening", "percentage": 45, "index_vs_coffee": 125, "index_vs_adults": 145 },
      { "hobby": "Craft/manual work", "percentage": 42, "index_vs_coffee": 136, "index_vs_adults": 154 },
      { "hobby": "Walking/hiking/rambling", "percentage": 42, "index_vs_coffee": 122, "index_vs_adults": 140 },
      { "hobby": "DIY, decorating", "percentage": 35, "index_vs_coffee": 158, "index_vs_adults": 176 },
      { "hobby": "Photography", "percentage": 24, "index_vs_coffee": 124, "index_vs_adults": 132 },
      { "hobby": "Playing board games, cards", "percentage": 22, "index_vs_coffee": 120, "index_vs_adults": 121 },
      { "hobby": "Attend a library, media library", "percentage": 16, "index_vs_coffee": 123, "index_vs_adults": 131 },
      { "hobby": "Computing/technology", "percentage": 12, "index_vs_coffee": 157, "index_vs_adults": 147 },
      { "hobby": "Other outdoor activities", "percentage": 11, "index_vs_coffee": 122, "index_vs_adults": 129 }
    ],
    "leisure_attitudes": [
      { "statement": "I really enjoy cooking", "percentage": 82, "index_vs_coffee": 132, "index_vs_adults": 145 },
      { "statement": "I am interested in other cultures", "percentage": 77, "index_vs_coffee": 125, "index_vs_adults": 128 },
      { "statement": "I am interested in international events", "percentage": 70, "index_vs_coffee": 127, "index_vs_adults": 131 },
      { "statement": "I am interested in the arts", "percentage": 69, "index_vs_coffee": 127, "index_vs_adults": 133 },
      { "statement": "Music is an important part of my life", "percentage": 59, "index_vs_coffee": 123, "index_vs_adults": 121 }
    ],
    "sports": {
      "interest_in_sports": [
        { "sport": "Football/soccer", "percentage": 45, "index_vs_coffee": 114, "index_vs_adults": 110 },
        { "sport": "Tennis", "percentage": 31, "index_vs_coffee": 114, "index_vs_adults": 117 },
        { "sport": "Motor sports (e.g. motorcycle/racing)", "percentage": 24, "index_vs_coffee": 110, "index_vs_adults": 106 },
        { "sport": "Formula 1", "percentage": 19, "index_vs_coffee": 115, "index_vs_adults": 112 },
        { "sport": "Moto Grand Prix", "percentage": 13, "index_vs_coffee": 138, "index_vs_adults": 132 },
        { "sport": "Motor Rallying/Rally Championships", "percentage": 12, "index_vs_coffee": 120, "index_vs_adults": 113 }
      ],
      "active_participation_sports": [
        { "sport": "Swimming", "percentage": 27, "index_vs_coffee": 140, "index_vs_adults": 146 },
        { "sport": "Mountain biking", "percentage": 21, "index_vs_coffee": 135, "index_vs_adults": 130 },
        { "sport": "Bowls", "percentage": 15, "index_vs_coffee": 124, "index_vs_adults": 129 },
        { "sport": "Skiing", "percentage": 15, "index_vs_coffee": 123, "index_vs_adults": 118 },
        { "sport": "Alpine skiing (piste)", "percentage": 13, "index_vs_coffee": 126, "index_vs_adults": 119 },
        { "sport": "Tennis", "percentage": 11, "index_vs_coffee": 164, "index_vs_adults": 160 }
      ],
      "active_participation_fitness": [
        { "activity": "Jogging/running", "percentage": 18, "index_vs_coffee": 145, "index_vs_adults": 134 },
        { "activity": "Aerobic/fitness classes", "percentage": 17, "index_vs_coffee": 134, "index_vs_adults": 139 },
        { "activity": "Weight training/weight machines", "percentage": 14, "index_vs_coffee": 136, "index_vs_adults": 118 },
        { "activity": "Yoga", "percentage": 13, "index_vs_coffee": 130, "index_vs_adults": 141 },
        { "activity": "Cardio machines (e.g. treadmill)", "percentage": 9, "index_vs_coffee": 129, "index_vs_adults": 121 },
        { "activity": "Pilates", "percentage": 8, "index_vs_coffee": 141, "index_vs_adults": 152 }
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
      },
      {
        "channel": "Social Media",
        "penetration_percentage": 84,
        "index_vs_coffee_drinkers": 111,
        "index_vs_all_adults": 112
      },
      {
        "channel": "TV",
        "penetration_percentage": 100,
        "index_vs_coffee_drinkers": 100,
        "index_vs_all_adults": 100
      },
      {
        "channel": "Magazines",
        "penetration_percentage": 73,
        "index_vs_coffee_drinkers": 111,
        "index_vs_all_adults": 120
      },
      {
        "channel": "Radio",
        "penetration_percentage": 92,
        "index_vs_coffee_drinkers": 103,
        "index_vs_all_adults": 106
      },
      {
        "channel": "Newspapers",
        "penetration_percentage": 67,
        "index_vs_coffee_drinkers": 109,
        "index_vs_all_adults": 118
      },
      {
        "channel": "Cinema",
        "penetration_percentage": 64,
        "index_vs_coffee_drinkers": 126,
        "index_vs_all_adults": 127
      }
    ],
    "technology_attitudes": [
      {
        "statement": "I like to have technology that makes life easier at home",
        "agreement_percentage": 73,
        "index_vs_coffee_drinkers": 128,
        "index_vs_all_adults": 129
      },
      {
        "statement": "I try to keep up with developments in technology",
        "agreement_percentage": 64,
        "index_vs_coffee_drinkers": 149,
        "index_vs_all_adults": 147
      },
      {
        "statement": "It is important for me to be able to synchronize all my electronic devices",
        "agreement_percentage": 47,
        "index_vs_coffee_drinkers": 140,
        "index_vs_all_adults": 139
      },
      {
        "statement": "I like innovative household devices/appliances",
        "agreement_percentage": 47,
        "index_vs_coffee_drinkers": 154,
        "index_vs_all_adults": 171
      },
      {
        "statement": "I love to buy new gadgets and appliances",
        "agreement_percentage": 40,
        "index_vs_coffee_drinkers": 209,
        "index_vs_all_adults": 190
      },
      {
        "statement": "It is important my household is equipped with the latest technology",
        "agreement_percentage": 37,
        "index_vs_coffee_drinkers": 152,
        "index_vs_all_adults": 141
      },
      {
        "statement": "Human interaction has improved through technology",
        "agreement_percentage": 22,
        "index_vs_coffee_drinkers": 131,
        "index_vs_all_adults": 120
      },
      {
        "statement": "I like to keep up with the latest news and developments in the video games industry/community",
        "agreement_percentage": 21,
        "index_vs_coffee_drinkers": 149,
        "index_vs_all_adults": 114
      }
    ],
    "channel_usage_intensity": [
      {
        "channel": "Internet",
        "usage_level": "Heavy users",
        "percentage": 19,
        "index_vs_coffee_drinkers": 133,
        "index_vs_all_adults": 127
      },
      {
        "channel": "Outdoor poster exposure",
        "usage_level": "Medium - travel 9 - 12 hours a week",
        "percentage": 22,
        "index_vs_coffee_drinkers": 125,
        "index_vs_all_adults": 130
      },
      {
        "channel": "Television",
        "usage_level": "Heavy Users",
        "percentage": 32,
        "index_vs_coffee_drinkers": 108,
        "index_vs_all_adults": 126
      },
      {
        "channel": "Magazines",
        "usage_level": "Heavy users (6+ hrs per week)",
        "percentage": 5,
        "index_vs_coffee_drinkers": 138,
        "index_vs_all_adults": 148
      },
      {
        "channel": "Radio",
        "usage_level": "Medium users",
        "percentage": 21,
        "index_vs_coffee_drinkers": 115,
        "index_vs_all_adults": 126
      },
      {
        "channel": "Newspapers",
        "usage_level": "Medium users (3-7 hrs per week)",
        "percentage": 11,
        "index_vs_coffee_drinkers": 122,
        "index_vs_all_adults": 132
      },
      {
        "channel": "Cinema",
        "usage_level": "Heavy users",
        "percentage": 27,
        "index_vs_coffee_drinkers": 143,
        "index_vs_all_adults": 150
      }
    ],
    "content_preferences": {
      "television_genres": [
        { "genre": "Sci-fi/fantasy", "percentage": 28, "index_vs_coffee_drinkers": 137, "index_vs_all_adults": 139 },
        { "genre": "Talent competition shows (e.g. X Factor)", "percentage": 21, "index_vs_coffee_drinkers": 120, "index_vs_all_adults": 133 },
        { "genre": "Property/DIY", "percentage": 17, "index_vs_coffee_drinkers": 121, "index_vs_all_adults": 138 }
      ],
      "film_genres": [
        { "genre": "Action", "percentage": 18, "index_vs_coffee_drinkers": 140, "index_vs_all_adults": 128 },
        { "genre": "Crime/thrillers/mystery", "percentage": 14, "index_vs_coffee_drinkers": 147, "index_vs_all_adults": 172 },
        { "genre": "Adventure", "percentage": 13, "index_vs_coffee_drinkers": 145, "index_vs_all_adults": 144 }
      ],
      "podcast_genres": [
        { "genre": "On-demand programmes", "percentage": 20, "index_vs_coffee_drinkers": 125, "index_vs_all_adults": 128 },
        { "genre": "Radio Programmes", "percentage": 17, "index_vs_coffee_drinkers": 140, "index_vs_all_adults": 147 },
        { "genre": "News & Politics", "percentage": 12, "index_vs_coffee_drinkers": 140, "index_vs_all_adults": 151 }
      ],
      "radio_programmes": [
        { "genre": "Generalist radio stations – Mornings", "percentage": 44, "index_vs_coffee_drinkers": 120, "index_vs_all_adults": 129 },
        { "genre": "Musical radio stations – Mornings", "percentage": 43, "index_vs_coffee_drinkers": 128, "index_vs_all_adults": 130 },
        { "genre": "Chroniques", "percentage": 26, "index_vs_coffee_drinkers": 122, "index_vs_all_adults": 136 }
      ],
      "newspaper_topics": [
        { "topic": "National news", "percentage": 36, "index_vs_coffee_drinkers": 152, "index_vs_all_adults": 171 },
        { "topic": "Recipes", "percentage": 36, "index_vs_coffee_drinkers": 168, "index_vs_all_adults": 200 },
        { "topic": "Regional news", "percentage": 36, "index_vs_coffee_drinkers": 139, "index_vs_all_adults": 159 }
      ]
    },
    "internet_consumption_profile": {
    "social_media_behavior": {
      "time_spent_frequency": [
        { "frequency": "More than 10 times a day", "percentage": 15, "vs_coffee_drinkers": "Higher" },
        { "frequency": "About 10 times a day", "percentage": 20, "vs_coffee_drinkers": "Higher" },
        { "frequency": "About 5 times a day", "percentage": 22, "vs_coffee_drinkers": "Similar" },
        { "frequency": "One a day", "percentage": 14, "vs_coffee_drinkers": "Similar" },
        { "frequency": "1-2 times a week", "percentage": 6, "vs_coffee_drinkers": "Higher" }
      ],
      "brands_used": [
        { "platform": "Pinterest", "penetration": 29, "index_vs_coffee": 148, "index_vs_adults": 159 },
        { "platform": "Snapchat", "penetration": 27, "index_vs_coffee": 133, "index_vs_adults": 109 },
        { "platform": "Instagram", "penetration": 46, "index_vs_coffee": 132, "index_vs_adults": 123 },
        { "platform": "YouTube", "penetration": 59, "index_vs_coffee": 127, "index_vs_adults": 124 }
      ]
    },
    "online_research_topics": [
      { "topic": "Food", "percentage": 43, "description": "compare vs 32% Total Coffee Drinkers" },
      { "topic": "Travel/holidays", "percentage": 34, "description": "compare vs 26% Total Coffee Drinkers" },
      { "topic": "Music", "percentage": 33, "description": "compare vs 26% Total Coffee Drinkers" },
      { "topic": "DIY and gardening", "percentage": 32, "description": "compare vs 24% Total Coffee Drinkers" },
      { "topic": "Home décor", "percentage": 29, "description": "compare vs 20% Total Coffee Drinkers" },
      { "topic": "Cinema and films", "percentage": 28, "description": "compare vs 20% Total Coffee Drinkers" },
      { "topic": "Politics", "percentage": 27, "description": "compare vs 21% Total Coffee Drinkers" },
      { "topic": "Academic study", "percentage": 26, "description": "compare vs 21% Total Coffee Drinkers" },
      { "topic": "The environment", "percentage": 25, "description": "compare vs 18% Total Coffee Drinkers" }
    ],
    "device_usage": [
      { "device": "Smart Speaker", "penetration": 9, "index_vs_coffee": 193, "index_vs_adults": 187 },
      { "device": "Smart Watch", "penetration": 6, "index_vs_coffee": 160, "index_vs_adults": 158 },
      { "device": "Smart TV", "penetration": 17, "index_vs_coffee": 143, "index_vs_adults": 133 },
      { "device": "Home games console", "penetration": 8, "index_vs_coffee": 137, "index_vs_adults": 109 },
      { "device": "Games console", "penetration": 9, "index_vs_coffee": 130, "index_vs_adults": 102 },
      { "device": "Tablet", "penetration": 36, "index_vs_coffee": 123, "index_vs_adults": 133 }
    ],
    "website_visitation_last_4_weeks": [
      { "site": "Expedia", "penetration": 9, "index_vs_coffee": 199, "index_vs_adults": 225 },
      { "site": "IKEA", "penetration": 27, "index_vs_coffee": 152, "index_vs_adults": 170 },
      { "site": "Twitter", "penetration": 19, "index_vs_coffee": 152, "index_vs_adults": 136 },
      { "site": "Ebay", "penetration": 18, "index_vs_coffee": 136, "index_vs_adults": 149 },
      { "site": "Wikipedia", "penetration": 31, "index_vs_coffee": 130, "index_vs_adults": 131 },
      { "site": "Carrefour", "penetration": 30, "index_vs_coffee": 127, "index_vs_adults": 148 },
      { "site": "YouTube", "penetration": 53, "index_vs_coffee": 126, "index_vs_adults": 127 }
    ],
    "online_activities_daily": [
      { "activity": "Make internet or video calls", "penetration": 16, "index_vs_coffee": 140 },
      { "activity": "Use Instant messaging", "penetration": 45, "index_vs_coffee": 131 },
      { "activity": "Use a search engine", "penetration": 60, "index_vs_coffee": 126 },
      { "activity": "Read or send personal e-mail", "penetration": 57, "index_vs_coffee": 121 }
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

#### **`types_of_coffee_drinks_consumedS`**

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

Nested structure with sub-brand metrics.

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