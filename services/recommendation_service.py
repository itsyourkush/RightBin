"""
Disposal and Recycling Recommendation Service.
Provides environmental guidelines, specific waste sub-type identification,
resin identification codes, decomposition timelines, environmental hazards,
conservation benefits, and shareable educational notes for eco-advocacy.
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional
import numpy as np
from PIL import Image


class RecommendationService:
    # Detailed sub-type catalog for fine-grained waste classification
    SUBTYPES_CATALOG: Dict[str, List[Dict[str, Any]]] = {
        "Plastic": [
            {
                "id": "plastic_pet",
                "subtype_name": "PET Beverage Bottle (Type 1 ♳)",
                "resin_code": "♳ PETE (1)",
                "material_type": "Polyethylene Terephthalate",
                "recyclability_score": "100% Widely Recyclable",
                "common_examples": "Water bottles, soda bottles, juice containers, clear food domes",
                "preparation_action": "Empty liquids completely, squeeze/crush bottle to save bin volume, replace cap.",
                "contamination_warning": "Remove PVC shrink sleeves and straws; unrinsed sweet liquids attract pests.",
                "environmental_impact": "Recycling 1 ton of PET saves 1.5 tons of CO2 and 5.7 cubic meters of landfill space.",
                "decomposition_time": "450 - 1,000 Years",
                "hazard_if_neglected": (
                    "Plastic bottles never truly biodegrade. Under sunlight, they break down into toxic microplastics "
                    "that absorb chemical pollutants and infiltrate our drinking water aquifers, marine ecosystems, and human food supply."
                ),
                "how_sorting_protects": (
                    "Placing this in the Blue Bin allows the polymer to be flaked, sanitized, and re-spun into new food-grade bottles "
                    "or polyester fibers, slashing greenhouse gas emissions by 71% and conserving crude oil feedstocks."
                ),
                "shareable_advocacy_note": (
                    "“Did you know a single plastic bottle takes 450 years to break down? Throwing it in the Blue Bin saves 70% of the energy "
                    "needed for new plastic and stops toxic microplastics from contaminating our drinking water!”"
                ),
            },
            {
                "id": "plastic_hdpe",
                "subtype_name": "HDPE Milk / Detergent Jug (Type 2 ♴)",
                "resin_code": "♴ HDPE (2)",
                "material_type": "High-Density Polyethylene",
                "recyclability_score": "100% Widely Recyclable",
                "common_examples": "Milk jugs, shampoo/conditioner bottles, detergent jugs, bleach containers",
                "preparation_action": "Rinse thoroughly to remove detergent or milk residue, replace screw cap, place in Blue Bin.",
                "contamination_warning": "Hazardous chemical or motor oil containers must go to toxic waste depots.",
                "environmental_impact": "Takes 88% less energy to recycle than manufacturing virgin resin from crude oil.",
                "decomposition_time": "400+ Years",
                "hazard_if_neglected": (
                    "Heavy-duty HDPE containers sit permanently in landfills, while unrinsed cleaning chemicals leach "
                    "toxic surfactants and endocrine disruptors into subterranean soil layers and groundwater."
                ),
                "how_sorting_protects": (
                    "Using the Blue Bin conserves 88% of manufacturing energy compared to virgin petroleum and redirects the resin "
                    "into long-lasting municipal agricultural drainage pipes, sturdy park benches, and reusable crates."
                ),
                "shareable_advocacy_note": (
                    "“Recycling this milk or detergent jug takes 88% less energy than refining crude oil for virgin plastic, "
                    "and prevents harmful chemical residues from poisoning our local soil!”"
                ),
            },
            {
                "id": "plastic_pp",
                "subtype_name": "PP Food Tub / Container (Type 5 ♷)",
                "resin_code": "♷ PP (5)",
                "material_type": "Polypropylene",
                "recyclability_score": "Widely Recyclable",
                "common_examples": "Yogurt containers, margarine tubs, syrup bottles, medicine vials, bottle caps",
                "preparation_action": "Scrape remaining food and rinse with cold water; stack containers together.",
                "contamination_warning": "Greasy takeout oils contaminate recycling pulpers—wash clean before binning.",
                "environmental_impact": "Reincarnated into heavy-duty storage bins, vehicle battery cases, and bicycle racks.",
                "decomposition_time": "20 - 30 Years",
                "hazard_if_neglected": (
                    "Resistant to bacterial decay, littered polypropylene containers clog storm sewers and fragment into urban debris, "
                    "releasing hazardous polyolefin chemicals when incinerated in open landfills."
                ),
                "how_sorting_protects": (
                    "Diverts polymers from municipal incinerators, capturing clean resin pellets for durable automotive battery cases, "
                    "heavy toolboxes, and community bicycle racks."
                ),
                "shareable_advocacy_note": (
                    "“Rinsing and sorting polypropylene containers keeps hazardous smoke out of the air and converts everyday plastic "
                    "into heavy-duty automotive battery cases and community bicycle racks!”"
                ),
            },
            {
                "id": "plastic_film",
                "subtype_name": "LDPE Soft Plastic / Film (Type 4 ♶)",
                "resin_code": "♶ LDPE (4)",
                "material_type": "Low-Density Polyethylene",
                "recyclability_score": "Special Drop-Off Only",
                "common_examples": "Grocery shopping bags, bubble wrap, bread bags, shrink wrap",
                "preparation_action": "Do NOT place in standard curbside bin (jams sorting rollers); return to grocery drop-off bin.",
                "contamination_warning": "Soft films tangle conveyor belts at automated sorting facilities.",
                "environmental_impact": "Reprocessed into composite eco-decking and recycled trash liners.",
                "decomposition_time": "500+ Years",
                "hazard_if_neglected": (
                    "Lightweight plastic films blow easily in the wind, suffocating terrestrial wildlife, choking marine turtles "
                    "who mistake them for jellyfish, and clogging municipal drainage gutters."
                ),
                "how_sorting_protects": (
                    "Clean collection channels fuse thin LDPE films into weather-resistant composite timber decking, saving trees "
                    "and preventing plastic from entering river deltas."
                ),
                "shareable_advocacy_note": (
                    "“Plastic grocery bags easily fly into rivers and choke marine wildlife. Bringing them to soft-plastic drop-offs "
                    "keeps waterways clean and turns them into composite park benches!”"
                ),
            },
        ],
        "Glass": [
            {
                "id": "glass_amber",
                "subtype_name": "Amber / Brown Glass Bottle (GL-72)",
                "resin_code": "GL-72",
                "material_type": "Amber Container Glass",
                "recyclability_score": "100% Infinitely Recyclable",
                "common_examples": "Beer bottles, kombucha bottles, pharmaceutical syrup containers",
                "preparation_action": "Rinse bottle, remove metal crown caps (recycle with metal), place in Glass Bin.",
                "contamination_warning": "Do not break intentionally; unbroken glass is safer and easier to sort.",
                "environmental_impact": "Every 1 ton of glass recycled saves 1.2 tons of virgin silica raw materials.",
                "decomposition_time": "1,000,000+ Years (Never Naturally Biodegrades)",
                "hazard_if_neglected": (
                    "Glass will never naturally decompose in human history. Throwing it in general garbage permanently wastes "
                    "precious landfill capacity and squanders the enormous fossil fuels spent mining raw silica."
                ),
                "how_sorting_protects": (
                    "Glass is 100% endlessly recyclable with ZERO loss in purity. Using cullet reduces kiln furnace temperatures, "
                    "cutting carbon dioxide emissions by 30% and eliminating mining impacts."
                ),
                "shareable_advocacy_note": (
                    "“Glass takes over 1 million years to decompose! But if we put it in the Glass Bin, it can be remelted "
                    "and back on store shelves as a new bottle in just 30 days without producing any toxic waste.”"
                ),
            },
            {
                "id": "glass_green",
                "subtype_name": "Green Glass Wine Bottle (GL-71)",
                "resin_code": "GL-71",
                "material_type": "Green Container Glass",
                "recyclability_score": "100% Infinitely Recyclable",
                "common_examples": "Wine bottles, olive oil bottles, sparkling cider bottles",
                "preparation_action": "Remove cork and foil neck sleeve, rinse interior with water, place in Glass Bin.",
                "contamination_warning": "Window glass, Pyrex cookware, and mirrors have different melting points and destroy glass batches.",
                "environmental_impact": "Can be remanufactured into a brand new glass container in under 30 days.",
                "decomposition_time": "1,000,000+ Years",
                "hazard_if_neglected": (
                    "Discarded in nature, glass bottles act as optical lenses that can focus sunlight and ignite forest wildfires. "
                    "Broken shards present severe cut hazards to sanitation workers, pedestrians, and animals."
                ),
                "how_sorting_protects": (
                    "Saves 1.2 tons of virgin natural silica sand and limestone for every ton recycled, protecting natural riverbeds "
                    "and coastal ecosystems from commercial dredging."
                ),
                "shareable_advocacy_note": (
                    "“Recycling just 1 glass bottle saves enough electricity to power a laptop for 25 minutes, "
                    "and prevents destructive silica mining from dredging our natural riverbeds!”"
                ),
            },
            {
                "id": "glass_clear",
                "subtype_name": "Clear Flint Glass Food Jar (GL-70)",
                "resin_code": "GL-70",
                "material_type": "Clear Flint Container Glass",
                "recyclability_score": "100% Infinitely Recyclable",
                "common_examples": "Jam jars, pasta sauce jars, pickle containers, baby food jars",
                "preparation_action": "Rinse food residues thoroughly, remove metal twist-off lid (recycle lid with metals).",
                "contamination_warning": "Ceramic dishes or heat-resistant glass must never enter the glass recycling stream.",
                "environmental_impact": "Zero degradation in physical properties no matter how many times it is remelted.",
                "decomposition_time": "1,000,000+ Years",
                "hazard_if_neglected": (
                    "Producing virgin clear glass requires intense industrial furnaces operating at 1,500°C, burning large amounts "
                    "of natural gas. Discarding glass after a single use causes unnecessary industrial air emissions."
                ),
                "how_sorting_protects": (
                    "Clear flint glass has the highest commercial demand. Every 10% of recycled cullet added to glass furnaces "
                    "lowers carbon dioxide emissions by 5% and extends furnace operating life."
                ),
                "shareable_advocacy_note": (
                    "“Did you know this glass jar can be recycled infinitely with zero loss in quality? "
                    "Recycling glass cuts furnace carbon emissions by over 20% compared to making glass from scratch!”"
                ),
            },
        ],
        "Metal": [
            {
                "id": "metal_aluminum_can",
                "subtype_name": "Aluminum Beverage Can (ALU-41)",
                "resin_code": "ALU-41",
                "material_type": "Beverage Can Aluminum",
                "recyclability_score": "100% Infinitely Recyclable",
                "common_examples": "Soda cans, sparkling water cans, energy drinks, beer cans",
                "preparation_action": "Empty residual liquid, leave pull-tab attached, place in Metal/Yellow Bin.",
                "contamination_warning": "Do not crush if your jurisdiction offers reverse vending deposit refunds.",
                "environmental_impact": "Recycling aluminum requires 95% less energy than mining and smelting virgin bauxite ore.",
                "decomposition_time": "200 - 500 Years",
                "hazard_if_neglected": (
                    "Mining virgin bauxite for aluminum requires massive open-pit deforestation and generates caustic toxic red mud "
                    "that threatens local watersheds. Discarding cans forces more ecologically devastating mining."
                ),
                "how_sorting_protects": (
                    "Recycling aluminum saves an extraordinary 95% of the electrical energy required to smelt new aluminum from raw ore. "
                    "An aluminum can is typically recycled and back on store shelves as a new can in only 60 days."
                ),
                "shareable_advocacy_note": (
                    "“Recycling just 1 aluminum can saves enough energy to power your TV for 3 hours! It takes 95% less energy "
                    "to recycle aluminum than to mine raw ore, protecting tropical forests from bauxite strip mining.”"
                ),
            },
            {
                "id": "metal_tin_can",
                "subtype_name": "Tin / Steel Food Can (FE-40)",
                "resin_code": "FE-40",
                "material_type": "Tin-Plated Steel",
                "recyclability_score": "100% Widely Recyclable",
                "common_examples": "Canned soup, canned vegetables, pet food tins, baked bean cans",
                "preparation_action": "Rinse food residue, push detached lid inside the can to prevent injuries, recycle in Metal Bin.",
                "contamination_warning": "Paint cans with wet chemical residue require hazardous waste drop-off.",
                "environmental_impact": "Steel is the most magnetically separated and recycled metal in modern sorting facilities.",
                "decomposition_time": "50 - 100 Years",
                "hazard_if_neglected": (
                    "Steel tins slowly rust and leach oxidized iron into municipal runoff, wasting refined iron ore and high-grade "
                    "metallurgical coking coal that produced the steel."
                ),
                "how_sorting_protects": (
                    "Modern sorting facilities extract steel cans effortlessly with overhead industrial electromagnets. Recycling steel "
                    "conserves 75% of production energy, 40% of industrial water, and 85% of factory air emissions."
                ),
                "shareable_advocacy_note": (
                    "“Steel cans are 100% magnetic and infinitely recyclable! Dropping this can in the metal bin saves iron ore "
                    "and cuts industrial factory air pollution by 85%!”"
                ),
            },
            {
                "id": "metal_aerosol",
                "subtype_name": "Aerosol Spray Can (FE-40/ALU-41)",
                "resin_code": "FE-40 / ALU-41",
                "material_type": "Pressurized Steel/Aluminum",
                "recyclability_score": "Recyclable When Depressurized",
                "common_examples": "Deodorant spray cans, hairspray, whipped cream, aerosol disinfectant",
                "preparation_action": "Ensure can is 100% empty and depressurized (no hissing when valve pressed); remove plastic cap.",
                "contamination_warning": "Never puncture or heat pressurized aerosol cans; explosive hazard in balers.",
                "environmental_impact": "Empty aerosol metal cans are safely compacted and smelted into new steel beams.",
                "decomposition_time": "100 - 200 Years",
                "hazard_if_neglected": (
                    "Pressurized cans thrown into regular waste trucks can puncture, explode, and injure sanitation workers or trigger "
                    "fires in mechanical trash compactors."
                ),
                "how_sorting_protects": (
                    "Fully emptied cans are safely processed in municipal metal balers, recovering structural-grade steel and aluminum "
                    "for heavy manufacturing and infrastructure construction."
                ),
                "shareable_advocacy_note": (
                    "“Making sure aerosol cans are completely empty and sorted protects sanitation workers from explosive fires "
                    "and recovers high-grade steel that can build new bridges!”"
                ),
            },
        ],
        "Paper": [
            {
                "id": "paper_cardboard",
                "subtype_name": "Corrugated Cardboard Box (PAP-20)",
                "resin_code": "PAP-20",
                "material_type": "Corrugated Paperboard",
                "recyclability_score": "100% Widely Recyclable",
                "common_examples": "Amazon/courier shipping boxes, packing boxes, double-wall boxes",
                "preparation_action": "Remove plastic packaging tape and labels, flatten boxes completely, keep dry.",
                "contamination_warning": "Greasy pizza boxes with heavy oil stains cannot be recycled and belong in compost or trash.",
                "environmental_impact": "Recycling 1 ton of corrugated cardboard saves 17 trees, 4,000 kW of electricity, and 7,000 gal water.",
                "decomposition_time": "2 Months (Years if compacted anaerobically in Landfills)",
                "hazard_if_neglected": (
                    "When cardboard is buried in airtight landfills, it breaks down without oxygen and generates Methane (CH4)—a greenhouse "
                    "gas 28 times more potent than carbon dioxide at trapping heat in our atmosphere."
                ),
                "how_sorting_protects": (
                    "Every ton of cardboard recycled saves 17 mature trees, 7,000 gallons of fresh water, and 4,000 kWh of electrical energy, "
                    "providing clean repulped fibers for new shipping boxes."
                ),
                "shareable_advocacy_note": (
                    "“Flattening and recycling this cardboard box saves forest trees and stops it from rotting into potent methane gas "
                    "inside municipal landfills. It takes 75% less energy to make new boxes from recycled cardboard!”"
                ),
            },
            {
                "id": "paper_office",
                "subtype_name": "Mixed Office / Notebook Paper (PAP-21)",
                "resin_code": "PAP-21",
                "material_type": "High-Grade Woodfree Paper",
                "recyclability_score": "100% High Recyclability",
                "common_examples": "Printer documents, notebook pages, letter paper, envelopes",
                "preparation_action": "Keep clean and dry; staples and paperclips are easily filtered by hydrapulper magnets.",
                "contamination_warning": "Thermal receipts contain BPA/BPS chemicals and must go into landfill trash, not recycling.",
                "environmental_impact": "Long virgin wood fibers can be repulped and recycled up to 7 successive times.",
                "decomposition_time": "2 - 6 Weeks",
                "hazard_if_neglected": (
                    "Virgin paper mills are among the highest industrial consumers of fresh water and energy worldwide, consuming vast "
                    "timber tracts and chemical bleaches that contaminate freshwater basins."
                ),
                "how_sorting_protects": (
                    "High-grade white paper fibers can be recycled up to 7 times. Recycling saves 65% of the energy and 80% of the water "
                    "needed to manufacture paper from raw timber."
                ),
                "shareable_advocacy_note": (
                    "“Paper fibers can be recycled up to 7 times! Recycling this paper saves freshwater supplies, cuts chemical bleaching, "
                    "and keeps our native forests standing tall.”"
                ),
            },
            {
                "id": "paper_newspaper",
                "subtype_name": "Newspaper & Newsprint (PAP-22)",
                "resin_code": "PAP-22",
                "material_type": "Mechanical Pulp Newsprint",
                "recyclability_score": "100% High Recyclability",
                "common_examples": "Daily newspapers, community gazettes, advertising flyers (unglazed)",
                "preparation_action": "Bundle together or stack flat inside paper recycling bin; keep dry.",
                "contamination_warning": "Waxed or laminated paper cannot be digested by paper mill recycling pulpers.",
                "environmental_impact": "Newsprint de-inking creates clean fiber for recycled packaging and egg cartons.",
                "decomposition_time": "6 Weeks",
                "hazard_if_neglected": (
                    "Decomposing newspaper inks and fibers in landfills generate acidic leachate that can contaminate surrounding waterways."
                ),
                "how_sorting_protects": (
                    "De-inked newsprint is swiftly converted into protective packaging, egg cartons, and recycled paperboard, "
                    "displacing virgin pulp production entirely."
                ),
                "shareable_advocacy_note": (
                    "“Recycling daily newsprint saves timber forests and turns old reading material into eco-friendly egg cartons "
                    "and home insulation!”"
                ),
            },
        ],
        "Organic": [
            {
                "id": "organic_produce",
                "subtype_name": "Fruit & Vegetable Food Scraps",
                "resin_code": "FOR-50",
                "material_type": "Biodegradable Organic Biomass",
                "recyclability_score": "100% Compostable",
                "common_examples": "Banana peels, apple cores, potato peelings, citrus rinds, salad trimmings",
                "preparation_action": "Remove plastic produce stickers and rubber bands; deposit in Compost / Green Bin.",
                "contamination_warning": "Never mix plastic cutlery, plastic produce bags, or stickers into organic waste.",
                "environmental_impact": "Prevents anaerobic landfill decomposition, cutting methane emissions and regenerating soil.",
                "decomposition_time": "2 - 8 Weeks (Compost) vs 25+ Years in Compacted Landfills",
                "hazard_if_neglected": (
                    "Food scraps thrown into regular trash end up buried in airtight landfills where they rot anaerobically, emitting "
                    "Methane (CH4) gas—a catastrophic contributor to global heating that traps 28 times more heat than CO2."
                ),
                "how_sorting_protects": (
                    "Depositing scraps in the Green Bin allows aerobic biological composting, converting organic waste into dark, "
                    "nutrient-dense compost that rejuvenates agricultural topsoil and locks carbon into the earth."
                ),
                "shareable_advocacy_note": (
                    "“Throwing food scraps in the trash creates methane gas that accelerates climate change. But in the Green Bin, "
                    "it turns into organic fertilizer that feeds new plants and restores our soil!”"
                ),
            },
            {
                "id": "organic_coffee",
                "subtype_name": "Coffee Grounds & Tea Leaves",
                "resin_code": "FOR-50",
                "material_type": "High-Nitrogen Organic Soil Amendment",
                "recyclability_score": "100% Compostable",
                "common_examples": "Used espresso coffee grounds, unbleached paper tea bags, coffee filters",
                "preparation_action": "Add directly to compost bin or garden soil as a high-nitrogen soil conditioner.",
                "contamination_warning": "Check tea bags: remove plastic nylon mesh bags (only paper bags compost).",
                "environmental_impact": "Natural pest deterrent and rich source of nitrogen, potassium, and phosphorus for crops.",
                "decomposition_time": "2 - 4 Weeks",
                "hazard_if_neglected": (
                    "Wastes valuable plant nutrients and contributes to foul anaerobic landfill odors and acidic leachate runoff."
                ),
                "how_sorting_protects": (
                    "Coffee grounds provide an ideal balance of nitrogen, potassium, and magnesium, naturally aerating topsoil, "
                    "deterring insect pests, and replacing chemical synthetic fertilizers."
                ),
                "shareable_advocacy_note": (
                    "“Coffee grounds are an incredible natural fertilizer! Putting them in the green bin keeps methane out of our skies "
                    "and nourishes gardens without chemical fertilizers.”"
                ),
            },
            {
                "id": "organic_grain",
                "subtype_name": "Bakery, Bread & Grain Scraps",
                "resin_code": "FOR-50",
                "material_type": "Carbohydrate Organic Waste",
                "recyclability_score": "100% Compostable",
                "common_examples": "Stale bread crusts, bagel ends, cooked rice, cereal leftovers",
                "preparation_action": "Add to compost bin or municipal organic collection container.",
                "contamination_warning": "Do not include plastic bread clips or twist ties.",
                "environmental_impact": "Fast-decomposing food biomass feeds composting microorganisms.",
                "decomposition_time": "1 - 2 Months",
                "hazard_if_neglected": (
                    "Rotting bakery carbohydrates in landfills attract vermin and generate methane greenhouse gas plumes."
                ),
                "how_sorting_protects": (
                    "Carbohydrate-rich grains feed beneficial composting microorganisms, accelerating the decomposition of tougher "
                    "yard trimmings into rich garden mulch."
                ),
                "shareable_advocacy_note": (
                    "“Every crumb of bread and grain we compost reduces landfill waste and feeds beneficial soil microbes "
                    "that keep our community green!”"
                ),
            },
        ],
    }

    # Authoritative knowledge base for base waste disposal guidance
    RECOMMENDATIONS: Dict[str, Dict[str, Any]] = {
        "Plastic": {
            "bin_type": "Recyclables / Blue Bin",
            "bin_color": "#1976D2",
            "decomposition_time": "450 - 1,000 Years",
            "hazard_if_neglected": (
                "Plastic waste never naturally biodegrades. Over centuries, sunlight breaks it into toxic microplastics "
                "that absorb environmental contaminants and poison marine and terrestrial food chains."
            ),
            "how_sorting_protects": (
                "Recycling plastic cuts petroleum usage by 70%, keeps synthetic polymers out of our oceans, "
                "and prevents toxic microplastics from contaminating drinking water."
            ),
            "shareable_advocacy_note": (
                "“Plastic takes 450+ years to break down! Putting it in the Blue Bin saves 70% energy and protects our drinking water from microplastics.”"
            ),
            "preparation_steps": [
                "Empty all residual liquid or food contents completely.",
                "Rinse lightly with minimal water to prevent mold in the recycling stream.",
                "Crush bottles to save space in the collection container.",
                "Remove non-recyclable plastic wrap or pumps if present.",
            ],
            "contamination_warnings": [
                "Dirty, grease-stained, or unrinsed plastic can contaminate entire recycling batches.",
                "Soft plastic bags or cling wrap often jam sorting machines—take these to specialized drop-off points.",
            ],
            "facility_note": (
                "PET (#1) and HDPE (#2) plastics are widely accepted. "
                "Check the resin code stamped on the bottom with your local municipal facility."
            ),
        },
        "Paper": {
            "bin_type": "Paper / Blue or Green Bin",
            "bin_color": "#2E7D32",
            "decomposition_time": "2 - 6 Weeks (Years if sealed in landfill)",
            "hazard_if_neglected": (
                "Buried paper rots without oxygen to generate Methane (CH4)—a gas 28x more damaging to the climate than CO2. "
                "Virgin paper production drives massive deforestation and freshwater consumption."
            ),
            "how_sorting_protects": (
                "Recycling 1 ton of paper saves 17 mature trees, 7,000 gallons of fresh water, and 4,000 kWh of electricity, "
                "and can be repulped up to 7 successive times."
            ),
            "shareable_advocacy_note": (
                "“Recycling paper saves forest trees, cuts water pollution by 35%, and stops paper from turning into potent methane in landfills!”"
            ),
            "preparation_steps": [
                "Keep paper completely clean and dry.",
                "Flatten cardboard boxes before disposal.",
                "Remove plastic tape, metallic staples, or plastic binding rings where practical.",
            ],
            "contamination_warnings": [
                "Greasy paper (such as oily pizza boxes) CANNOT be recycled via standard paper pulping.",
                "Wax-coated cups and thermal receipt paper contain BPA and belong in general waste.",
            ],
            "facility_note": (
                "Clean newsprint, office documents, and corrugated cardboard have high recycling value. "
                "Shredded paper should be bagged if required by your municipality."
            ),
        },
        "Organic": {
            "bin_type": "Compost / Green Bin",
            "bin_color": "#388E3C",
            "decomposition_time": "2 - 8 Weeks (Compost)",
            "hazard_if_neglected": (
                "Food waste in regular garbage rots anaerobically, generating explosive methane greenhouse gas and toxic acidic leachate."
            ),
            "how_sorting_protects": (
                "Aerobic composting transforms food scraps into rich humus that rejuvenates topsoil, retains water in droughts, "
                "and captures carbon in the ground."
            ),
            "shareable_advocacy_note": (
                "“Food in regular trash creates methane that warms our planet. In the Green Bin, it turns into rich organic soil that feeds new life!”"
            ),
            "preparation_steps": [
                "Remove any plastic stickers, price tags, or rubber bands from fruit and vegetable scraps.",
                "Drain excess liquids before adding to your compost or organic bin.",
                "Layer with dry leaves, paper, or sawdust if managing home compost.",
            ],
            "contamination_warnings": [
                "Never mix plastic cutlery, foil, or packaging with organic waste.",
                "Large bones, dairy, and oils may attract pests in home compost systems—check local municipal composting rules.",
            ],
            "facility_note": (
                "Composting organic waste prevents methane emissions in landfills and enriches topsoil."
            ),
        },
        "Metal": {
            "bin_type": "Metals / Yellow or Blue Bin",
            "bin_color": "#F57C00",
            "decomposition_time": "200 - 500 Years",
            "hazard_if_neglected": (
                "Discarding metals forces more open-pit bauxite strip mining, destroying tropical forests and producing caustic red mud runoff."
            ),
            "how_sorting_protects": (
                "Recycling aluminum saves an astonishing 95% of energy compared to mining raw ore. Metals are infinitely recyclable with zero quality loss."
            ),
            "shareable_advocacy_note": (
                "“Recycling 1 aluminum can saves enough power to run your TV for 3 hours! It takes 95% less energy to recycle than to mine new metal.”"
            ),
            "preparation_steps": [
                "Rinse aluminum beverage cans and steel food cans thoroughly.",
                "Leave the can lid attached or push it inside the can so it doesn't pose a laceration hazard.",
                "Do not puncture pressurized aerosol cans.",
            ],
            "contamination_warnings": [
                "Paint cans with wet chemical residue require hazardous waste drop-off.",
                "Pans or electronics with plastic handles should not go into standard curbside metal bins.",
            ],
            "facility_note": (
                "Metals (especially aluminum) are infinitely recyclable without degradation, saving 95% of energy compared to raw extraction."
            ),
        },
        "Glass": {
            "bin_type": "Glass / Green or Teal Bin",
            "bin_color": "#00897B",
            "decomposition_time": "1,000,000+ Years (Indestructible)",
            "hazard_if_neglected": (
                "Glass occupies permanent landfill space forever. Discarded bottles can focus sunlight and ignite wildfires, while broken shards endanger workers and wildlife."
            ),
            "how_sorting_protects": (
                "Glass is 100% infinitely recyclable. Remelting glass cullet uses 30% less furnace energy and saves natural silica sand from riverbed mining."
            ),
            "shareable_advocacy_note": (
                "“Glass takes 1 million years to decompose! Recycling it saves 30% furnace energy and can turn it into a new bottle in 30 days.”"
            ),
            "preparation_steps": [
                "Rinse glass jars and bottles thoroughly.",
                "Remove metal or plastic caps (recycle them separately).",
                "Do not intentionally break bottles; unbroken glass is safer and easier to sort.",
            ],
            "contamination_warnings": [
                "Window glass, mirrors, Pyrex, ceramics, and light bulbs have different melting points and will ruin batch glass melts.",
                "Broken glass shards can injure recycling workers and must be wrapped safely if put in general waste.",
            ],
            "facility_note": (
                "Glass containers can be recycled endlessly into new glass products without loss of purity or quality."
            ),
        },
    }

    FALLBACK_GUIDANCE = {
        "bin_type": "General Inspection / Safe Sorting",
        "bin_color": "#757575",
        "decomposition_time": "Varies by material",
        "hazard_if_neglected": "Unidentified waste can contaminate entire recycling batches, diverting valuable recyclable loads into landfills.",
        "how_sorting_protects": "Careful material inspection ensures only pure, non-contaminated materials enter processing streams.",
        "shareable_advocacy_note": "“When in doubt, check the recycling symbol before binning. Proper sorting prevents entire batches from ending up in the landfill!”",
        "preparation_steps": [
            "Examine item carefully for recycling symbols or resin identification codes.",
            "Separate multi-material components (e.g., plastic lid from glass jar).",
            "When in doubt, check with your local municipality rather than 'wishcycling'.",
        ],
        "contamination_warnings": [
            "Contaminated recycling streams cause entire truckloads to be diverted to landfills.",
        ],
        "facility_note": (
            "Because this classification is uncertain, verify item material directly before sorting."
        ),
    }

    def identify_subtype(
        self,
        category: str,
        image_bytes: Optional[bytes] = None,
        qr_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Identifies the specific waste sub-type, resin code, and recyclability details.
        Uses packaging QR code hints or image color profiles.
        """
        available = self.SUBTYPES_CATALOG.get(category, [])
        if not available:
            return {
                "id": f"{category.lower()}_generic",
                "subtype_name": f"Standard {category}",
                "resin_code": "Standard",
                "material_type": category,
                "recyclability_score": "Widely Recyclable",
                "common_examples": "General items in this category",
                "preparation_action": "Follow municipal disposal guidelines for this material.",
                "contamination_warning": "Clean and dry items before placing in recycling bins.",
                "environmental_impact": "Proper segregation reduces landfill volume and conserves raw materials.",
                "decomposition_time": "Varies",
                "hazard_if_neglected": "Contributes to landfill expansion and resource depletion.",
                "how_sorting_protects": "Recovers valuable secondary raw materials.",
                "shareable_advocacy_note": f"“Properly sorting {category} keeps our community clean and conserves energy!”",
            }

        # QR code matching
        if qr_content:
            q_lower = qr_content.lower()
            for st in available:
                if any(k in q_lower for k in st["id"].split("_")):
                    return st

        # Image color analysis
        if image_bytes:
            try:
                img = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((64, 64))
                arr = np.array(img)
                mean_r, mean_g, mean_b = arr[:, :, 0].mean(), arr[:, :, 1].mean(), arr[:, :, 2].mean()
                brightness = (mean_r + mean_g + mean_b) / 3.0

                if category == "Glass":
                    if mean_r > mean_g + 20 and mean_r > mean_b + 30:
                        return available[0]  # Amber / Brown
                    elif mean_g > mean_r + 10 and mean_g > mean_b:
                        return available[1]  # Green wine
                    else:
                        return available[2]  # Clear flint

                elif category == "Plastic":
                    if brightness > 220:
                        return available[0]  # Clear PET
                    elif brightness > 180:
                        return available[1]  # HDPE milk/detergent
                    else:
                        return available[2]  # PP food tub

                elif category == "Metal":
                    if brightness > 160:
                        return available[0]  # Aluminum beverage can
                    elif brightness > 110:
                        return available[1]  # Tin/steel food can
                    else:
                        return available[2]  # Aerosol can

                elif category == "Paper":
                    if mean_r > mean_b + 25 and mean_g > mean_b + 10:
                        return available[0]  # Corrugated cardboard box
                    elif brightness > 180:
                        return available[1]  # Office/writing paper
                    else:
                        return available[2]  # Newspaper

                elif category == "Organic":
                    if brightness < 90:
                        return available[1]  # Coffee grounds
                    elif mean_r > mean_b + 30 and mean_g > mean_b + 20:
                        return available[0]  # Fruit & vegetable scraps
                    else:
                        return available[2]  # Bakery & grain scraps

            except Exception:
                pass

        return available[0]

    def get_recommendation(
        self,
        category: str,
        is_accepted: bool = True,
        subtype_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Returns structured disposal instructions, specific sub-type details,
        decomposition timeline, environmental hazards, and shareable advocacy notes.
        """
        if not is_accepted or category not in self.RECOMMENDATIONS:
            guidance = dict(self.FALLBACK_GUIDANCE)
            guidance["category"] = category if category else "Uncertain"
            guidance["status"] = "low_confidence_fallback"
            guidance["sub_category"] = "Unspecified / Low Confidence"
            guidance["resin_code"] = "N/A"
            guidance["recyclability_score"] = "Unverified"
            return guidance

        guidance = dict(self.RECOMMENDATIONS[category])
        guidance["category"] = category
        guidance["status"] = "verified_recommendation"

        if subtype_info:
            guidance["sub_category"] = subtype_info.get("subtype_name", f"Standard {category}")
            guidance["resin_code"] = subtype_info.get("resin_code", "Standard")
            guidance["recyclability_score"] = subtype_info.get("recyclability_score", "Widely Recyclable")
            guidance["material_type"] = subtype_info.get("material_type", category)
            guidance["environmental_impact"] = subtype_info.get("environmental_impact", "")
            guidance["decomposition_time"] = subtype_info.get("decomposition_time", guidance.get("decomposition_time", "Varies"))
            guidance["hazard_if_neglected"] = subtype_info.get("hazard_if_neglected", guidance.get("hazard_if_neglected", ""))
            guidance["how_sorting_protects"] = subtype_info.get("how_sorting_protects", guidance.get("how_sorting_protects", ""))
            guidance["shareable_advocacy_note"] = subtype_info.get("shareable_advocacy_note", guidance.get("shareable_advocacy_note", ""))

            specific_prep = subtype_info.get("preparation_action")
            if specific_prep and specific_prep not in guidance["preparation_steps"]:
                guidance["preparation_steps"] = [specific_prep] + guidance["preparation_steps"]
        else:
            guidance["sub_category"] = f"Standard {category}"
            guidance["resin_code"] = "Standard"
            guidance["recyclability_score"] = "Widely Recyclable"

        return guidance
