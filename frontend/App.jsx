const { useEffect, useMemo, useRef, useState } = React;

const API_BASE = "http://127.0.0.1:5000";

const initialForm = {
  location: "",
  city: "",
  property_type: "",
  bedrooms: "",
  floor: "",
  facing: "",
  balcony: "",
  carpet_area: "",
  carpet_area_unit: "",
  original_carpet_area: "",
  original_carpet_area_unit: "",
  parking: "",
  garden_park: "",
  main_road: "",
  pool: "",
  gym: "",
  lift: "",
  power_backup: "",
  security: "",
};

const propertyFields = [
  ["city", "City", "select", true],
  ["location", "Location", "search", true],
  ["property_type", "Property Type", "select", true],
  ["bedrooms", "Bedrooms", "select", true],
  ["floor", "Floor", "select", false],
  ["facing", "Facing", "select", false],
  ["balcony", "Balcony", "select", false],
  ["parking", "Parking", "select", false],
  ["carpet_area", "Carpet Area", "area", false],
];

const amenityFields = [
  ["garden_park", "Garden/Park"],
  ["main_road", "Main Road"],
  ["pool", "Pool"],
  ["gym", "Gym"],
  ["lift", "Lift"],
  ["security", "Security"],
  ["power_backup", "Power Backup"],
];

function formatInr(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "N/A";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: numeric % 1 === 0 ? 0 : 2,
    maximumFractionDigits: 2,
  }).format(numeric);
}

function formatNumber(value, options = {}) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "N/A";
  return new Intl.NumberFormat("en-IN", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
    ...options,
  }).format(numeric);
}

function formatRate(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) return "N/A";
  return `₹${formatNumber(numeric, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatArea(value, unit = "sqft") {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) return "N/A";
  return `${formatNumber(numeric)} ${unit || "sqft"}`;
}

function rateLabel(unit = "sqft") {
  return `Rate per ${unit || "sqft"}`;
}

const AREA_SQFT_FACTORS = {
  sqft: 1,
  sqm: 10.7639,
  sqyrd: 9,
};

function convertArea(value, fromUnit = "sqft", toUnit = "sqft") {
  const numeric = Number(value);
  const fromFactor = AREA_SQFT_FACTORS[fromUnit] || 1;
  const toFactor = AREA_SQFT_FACTORS[toUnit] || fromFactor;
  if (!Number.isFinite(numeric) || numeric <= 0) return null;
  return (numeric * fromFactor) / toFactor;
}

function normalizeToSqft(value, unit = "sqft") {
  const numeric = Number(value);
  const factor = AREA_SQFT_FACTORS[unit] || 1;
  if (!Number.isFinite(numeric) || numeric <= 0) return null;
  return numeric * factor;
}

function convertRate(value, fromUnit = "sqft", toUnit = "sqft") {
  const numeric = Number(value);
  const fromFactor = AREA_SQFT_FACTORS[fromUnit] || 1;
  const toFactor = AREA_SQFT_FACTORS[toUnit] || fromFactor;
  if (!Number.isFinite(numeric) || numeric <= 0) return null;
  return (numeric / fromFactor) * toFactor;
}

function calculateTotalArea(carpetArea, loadingFactor = 1) {
  const area = Number(carpetArea);
  const factor = Number(loadingFactor);
  if (!Number.isFinite(area) || area <= 0) return null;
  return area * (Number.isFinite(factor) && factor > 0 ? factor : 1);
}

function formatDisplayValues(prediction, selectedUnit, enteredCarpetArea) {
  if (!prediction || prediction.error) return null;

  const originalUnit = prediction.original_carpet_area_unit || prediction.carpet_area_unit || "sqft";
  const displayUnit = selectedUnit || prediction.rate_unit || originalUnit;
  const originalCarpetArea = prediction.original_carpet_area || prediction.carpet_area;
  const displayCarpetArea = Number.isFinite(Number(enteredCarpetArea)) && Number(enteredCarpetArea) > 0
    ? Number(enteredCarpetArea)
    : Number(prediction.carpet_area);
  const loadingFactor = Number(prediction.loading_factor) > 0 ? Number(prediction.loading_factor) : 1;
  const rate = convertRate(
    prediction.original_rate || prediction.price_per_sqft,
    prediction.original_rate_unit || originalUnit,
    displayUnit
  );
  const amenityBoost = Number(prediction.amenity_price_boost?.total || 0);
  const isOriginalDatasetArea =
    displayUnit === originalUnit &&
    Number.isFinite(displayCarpetArea) &&
    Number.isFinite(Number(originalCarpetArea)) &&
    Math.abs(displayCarpetArea - Number(originalCarpetArea)) <= 0.01;
  const dynamicPrice =
    isOriginalDatasetArea
      ? prediction.base_dataset_price || prediction.predicted_price
      : displayCarpetArea * (rate || 0) + amenityBoost;

  return {
    unit: displayUnit,
    carpetArea: displayCarpetArea,
    totalArea: calculateTotalArea(displayCarpetArea, loadingFactor),
    rate: rate || prediction.price_per_sqft,
    predictedPrice: Number.isFinite(dynamicPrice) && dynamicPrice > 0 ? dynamicPrice : prediction.predicted_price,
    normalizedCarpetAreaSqft: normalizeToSqft(displayCarpetArea, displayUnit),
    normalizedTotalAreaSqft: normalizeToSqft(calculateTotalArea(displayCarpetArea, loadingFactor), displayUnit),
  };
}

function googleMapsUrl(locationLabel) {
  const encodedLocation = encodeURIComponent(locationLabel || "Delhi, India");
  return `https://www.google.com/maps/search/?api=1&query=${encodedLocation}`;
}

function App() {
  const [form, setForm] = useState(initialForm);
  const [options, setOptions] = useState({});
  const [locationOptions, setLocationOptions] = useState([]);
  const [dependentOptions, setDependentOptions] = useState({});
  const [inventory, setInventory] = useState({});
  const [demand, setDemand] = useState([]);
  const [properties, setProperties] = useState([]);
  const [prediction, setPrediction] = useState(null);
  const [isPredicting, setIsPredicting] = useState(false);
  const [loadingHome, setLoadingHome] = useState(true);
  const [authConfig, setAuthConfig] = useState({ google_client_id: "" });

  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  const searchDropdownRef = useRef(null);
  const [isLocationOpen, setIsLocationOpen] = useState(false);
  const [isCarpetAreaOpen, setIsCarpetAreaOpen] = useState(false);

  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("pricenest_user") || "null");
    } catch {
      return null;
    }
  });

  useEffect(() => {
    async function loadLocationsForCity() {
      if (!form.city) {
        setLocationOptions(options.location || []);
        setDependentOptions({});
        return;
      }

      try {
        const response = await fetch(`${API_BASE}/locations?city=${encodeURIComponent(form.city)}`);
        const data = await response.json();
        setLocationOptions(data.options || []);
      } catch (error) {
        console.error("Failed to load city locations:", error);
        setLocationOptions([]);
      }
    }

    loadLocationsForCity();
  }, [form.city, options.location]);

  useEffect(() => {
    async function loadDependentOptions() {
      if (!form.city || !form.location) {
        setDependentOptions({});
        return;
      }

      try {
        const params = new URLSearchParams({
          city: form.city,
          location: form.location,
          property_type: form.property_type,
          bedrooms: form.bedrooms,
          floor: form.floor,
          facing: form.facing,
          balcony: form.balcony,
          parking: form.parking,
          carpet_area: form.carpet_area,
          carpet_area_unit: form.carpet_area_unit,
          original_carpet_area: form.original_carpet_area,
          original_carpet_area_unit: form.original_carpet_area_unit,
        });
        const response = await fetch(`${API_BASE}/filter-options?${params.toString()}`);
        const data = await response.json();
        setDependentOptions(data || {});
      } catch (error) {
        console.error("Failed to load location filter options:", error);
        setDependentOptions({});
      }
    }

    loadDependentOptions();
  }, [form.city, form.location, form.property_type, form.bedrooms, form.floor, form.facing, form.balcony, form.parking, form.carpet_area, form.carpet_area_unit, form.original_carpet_area, form.original_carpet_area_unit]);

  useEffect(() => {
    if (!form.city || !form.location || form.carpet_area_unit) return;
    const firstOption = dependentOptions.carpet_area_options?.[0];
    if (firstOption?.unit) {
      setForm((prev) => (prev.carpet_area_unit ? prev : { ...prev, carpet_area_unit: firstOption.unit }));
    }
  }, [dependentOptions, form.city, form.location, form.carpet_area_unit]);

  // Debounced search for autocomplete suggestions
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (!query.trim()) {
        setSuggestions([]);
        setShowSuggestions(false);
        return;
      }

      setIsSearching(true);
      try {
        const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}&limit=8`);
        if (!response.ok) throw new Error("Search failed");
        const data = await response.json();
        setSuggestions(data.results || []);
        setShowSuggestions(true);
        setSelectedSuggestionIndex(-1);
      } catch (error) {
        console.error("Autocomplete search failed:", error);
        setSuggestions([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Handle outside click to close suggestions
  useEffect(() => {
    function handleClickOutside(event) {
      if (searchDropdownRef.current && !searchDropdownRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Handle keyboard navigation in suggestions
  useEffect(() => {
    function handleKeyDown(event) {
      if (!showSuggestions || suggestions.length === 0) return;

      switch (event.key) {
        case "ArrowDown":
          event.preventDefault();
          setSelectedSuggestionIndex((prev) => 
            prev < suggestions.length - 1 ? prev + 1 : 0
          );
          break;
        case "ArrowUp":
          event.preventDefault();
          setSelectedSuggestionIndex((prev) => 
            prev > 0 ? prev - 1 : suggestions.length - 1
          );
          break;
        case "Enter":
          event.preventDefault();
          if (selectedSuggestionIndex >= 0) {
            selectSuggestion(suggestions[selectedSuggestionIndex]);
          } else if (query.trim()) {
            performSearch();
          }
          break;
        case "Escape":
          setShowSuggestions(false);
          break;
        default:
          break;
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [showSuggestions, suggestions, selectedSuggestionIndex, query]);

  useEffect(() => {
    async function bootstrap() {
      setLoadingHome(true);
      try {
        const [optionsRes, inventoryRes, demandRes, propertiesRes] = await Promise.all([
          fetch(`${API_BASE}/options`),
          fetch(`${API_BASE}/inventory`),
          fetch(`${API_BASE}/demand`),
          fetch(`${API_BASE}/top-properties?limit=8`),
        ]);

        const optionsData = await optionsRes.json();
        const inventoryData = await inventoryRes.json();
        const demandData = await demandRes.json();
        const propertiesData = await propertiesRes.json();

        setOptions(optionsData.options || {});
        setInventory(inventoryData.inventory || inventoryData || {});
        setDemand(demandData.demand || []);
        setProperties(propertiesData.top_properties || propertiesData.properties || []);
      } catch (error) {
        console.error("Failed to load initial API data:", error);
      } finally {
        setLoadingHome(false);
      }
    }

    bootstrap();
  }, []);

  useEffect(() => {
    async function loadAuthConfig() {
      try {
        const response = await fetch(`${API_BASE}/auth/config`);
        const data = await response.json();
        setAuthConfig(data || {});
      } catch (error) {
        console.error("Failed to load auth config:", error);
      }
    }

    loadAuthConfig();
  }, []);

  const handleSearch = async () => {
    if (!query.trim()) return;
    performSearch();
  };

  const performSearch = async () => {
    setIsSearching(true);
    setShowSearchResults(true);
    setShowSuggestions(false);
    try {
      const response = await fetch(`${API_BASE}/search/properties?q=${encodeURIComponent(query)}&limit=20`);
      if (!response.ok) throw new Error("Search failed");
      const data = await response.json();
      setSearchResults(data.properties || []);
    } catch (error) {
      console.error("Search failed:", error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const selectSuggestion = async (suggestion) => {
    setQuery(suggestion.name || "");
    setSuggestions([]);
    setShowSuggestions(false);
    setShowSearchResults(true);

    try {
      const response = await fetch(
        `${API_BASE}/search/properties?q=${encodeURIComponent(suggestion.name)}&limit=20`
      );
      if (!response.ok) throw new Error("Search failed");
      const data = await response.json();
      setSearchResults(data.properties || []);
    } catch (error) {
      console.error("Failed to get full results:", error);
      setSearchResults([]);
    }
  };

  const selectedLocation = useMemo(
    () => [form.location, form.city].filter(Boolean).join(", ") || "Delhi, India",
    [form.city, form.location]
  );

  const mapLocation = useMemo(
    () =>
      prediction && !prediction.error
        ? [prediction.location, prediction.city].filter(Boolean).join(", ")
        : selectedLocation,
    [prediction, selectedLocation]
  );

  const selectedTotalArea = useMemo(() => {
    const option = dependentOptions.carpet_area_options?.find((item) => String(item.value) === String(form.carpet_area));
    if (!option?.total_area) return "";
    return convertArea(option.total_area, "sqft", form.carpet_area_unit || option.unit || "sqft");
  }, [dependentOptions, form.carpet_area, form.carpet_area_unit]);

  const selectedAmenities = useMemo(
    () =>
      amenityFields
        .filter(([key]) => form[key] === "Yes")
        .map(([, label]) => label),
    [form]
  );

  const predictionDisplay = useMemo(() => {
    return formatDisplayValues(prediction, form.carpet_area_unit, form.carpet_area);
  }, [prediction, form.carpet_area_unit, form.carpet_area]);

  const locationMatches = useMemo(() => {
    const query = form.location.trim().toLowerCase();
    const source = locationOptions || [];
    if (!query) return source;
    return source.filter((location) => location.toLowerCase().includes(query));
  }, [form.location, locationOptions]);

  const availableCarpetAreaOptions = useMemo(() => {
    const directOptions = dependentOptions.carpet_area_options || [];
    if (directOptions.length > 0) return directOptions;

    const valuesByUnit = dependentOptions.carpet_area_values_by_unit || {};
    return Object.entries(valuesByUnit).flatMap(([unit, values]) =>
      (values || []).map((value) => ({
        value: String(value),
        unit,
        label: `${value} ${unit}`,
        total_area: dependentOptions.total_area_by_carpet_area_unit?.[unit]?.[String(value)] || null,
      }))
    );
  }, [dependentOptions]);

  const carpetAreaMatches = useMemo(() => {
    const query = form.carpet_area.trim().toLowerCase();
    const source = availableCarpetAreaOptions;
    if (!query) return source;
    return source.filter((item) => String(item.value).toLowerCase().includes(query) || item.label.toLowerCase().includes(query));
  }, [availableCarpetAreaOptions, form.carpet_area]);

  function datasetAmenityValue(key) {
    if (!form.city || !form.location) return "";
    const values = dependentOptions[key] || [];
    if (values.includes("Yes")) return "Yes";
    if (values.includes("No")) return "No";
    return "Not Available";
  }

  function updateField(key, value) {
    const resetsByField = {
      city: { location: "", property_type: "", bedrooms: "", floor: "", balcony: "", facing: "", parking: "", carpet_area: "", carpet_area_unit: "", original_carpet_area: "", original_carpet_area_unit: "", garden_park: "", main_road: "", pool: "" },
      location: { property_type: "", bedrooms: "", floor: "", balcony: "", facing: "", parking: "", carpet_area: "", carpet_area_unit: "", original_carpet_area: "", original_carpet_area_unit: "", garden_park: "", main_road: "", pool: "" },
      property_type: { bedrooms: "", floor: "", balcony: "", facing: "", parking: "", carpet_area: "", carpet_area_unit: "", original_carpet_area: "", original_carpet_area_unit: "" },
      bedrooms: { floor: "", balcony: "", facing: "", parking: "", carpet_area: "", carpet_area_unit: "", original_carpet_area: "", original_carpet_area_unit: "" },
      floor: { balcony: "", facing: "", parking: "", carpet_area: "", carpet_area_unit: "", original_carpet_area: "", original_carpet_area_unit: "" },
      facing: { balcony: "", parking: "", carpet_area: "", carpet_area_unit: "", original_carpet_area: "", original_carpet_area_unit: "" },
      balcony: { parking: "", carpet_area: "", carpet_area_unit: "", original_carpet_area: "", original_carpet_area_unit: "" },
      parking: { carpet_area: "", carpet_area_unit: "", original_carpet_area: "", original_carpet_area_unit: "" },
      carpet_area: { original_carpet_area: "", original_carpet_area_unit: "" },
    };
    setForm((prev) => ({
      ...prev,
      [key]: value,
      ...(resetsByField[key] || {}),
    }));
  }

  function updateCarpetAreaUnit(value) {
    setForm((prev) => ({
      ...prev,
      carpet_area_unit: value,
    }));
  }

  function chooseSuggestion(item) {
    setQuery(item.label);
    setShowSuggestions(false);
    setForm((prev) => ({ ...prev, city: item.city || "", location: item.location || "" }));
  }

  async function onPredict(event) {
    event.preventDefault();
    setIsPredicting(true);
    setPrediction(null);

    try {
      if (form.location && !locationOptions.includes(form.location)) {
        throw new Error("Select a location that exists in the dataset.");
      }
      const allCarpetAreaValues = (dependentOptions.carpet_area_options || []).map((item) => String(item.value));
      if (form.carpet_area && allCarpetAreaValues.length > 0 && !allCarpetAreaValues.includes(String(form.carpet_area))) {
        throw new Error("Select a carpet area value that exists in the dataset.");
      }

      const payload = {
        ...form,
        carpet_area_sqft: form.carpet_area,
        original_carpet_area: form.original_carpet_area || availableCarpetAreaOptions.find((item) => String(item.value) === String(form.carpet_area))?.value || form.carpet_area,
        original_carpet_area_unit: form.original_carpet_area_unit || availableCarpetAreaOptions.find((item) => String(item.value) === String(form.carpet_area))?.unit || form.carpet_area_unit,
        property_name: `${form.bedrooms} BHK in ${form.location}, ${form.city}`,
      };
      const response = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Prediction request failed.");
      }
      setPrediction(data);
    } catch (error) {
      setPrediction({ error: error.message });
    } finally {
      setIsPredicting(false);
    }
  }

  function optionsForField(key) {
    if (key === "location") return locationOptions;
    if (["bedrooms", "floor", "balcony", "facing", "parking", "property_type", "garden_park", "main_road", "pool"].includes(key) && form.city && form.location) {
      return dependentOptions[key] || [];
    }
    return options[key] || [];
  }

  function carpetAreaOptionsForUnit(unit) {
    if (form.city && form.location) return (dependentOptions.carpet_area_options || []).map((item) => item.value);
    const filteredValues = dependentOptions.carpet_area_values_by_unit?.[unit];
    return options.carpet_area_values_by_unit?.[unit] || [];
  }

  function isDatasetFiltered() {
    return Boolean(form.city && form.location);
  }

  function isFieldUnavailable(key) {
    if (!isDatasetFiltered()) return false;
    if (key === "carpet_area") {
      const valuesByUnit = dependentOptions.carpet_area_values_by_unit || {};
      return ["sqft", "sqm", "sqyrd"].every((unit) => (valuesByUnit[unit] || []).length === 0);
    }
    if (["bedrooms", "floor", "balcony", "facing", "parking", "property_type", "garden_park", "main_road", "pool"].includes(key)) {
      return optionsForField(key).length === 0;
    }
    return false;
  }

  async function logout() {
    try {
      if (window.pricenestFirebase?.auth && window.pricenestFirebase?.signOut) {
        await window.pricenestFirebase.signOut(window.pricenestFirebase.auth);
      }
    } catch (error) {
      console.error("Firebase logout failed:", error);
    }
    localStorage.removeItem("pricenest_user");
    setCurrentUser(null);
    setIsProfileOpen(false);
    window.location.hash = "";
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function printDetails() {
    if (!prediction || prediction.error) return;

    const reportWindow = window.open("", "_blank", "width=900,height=1200");
    if (!reportWindow) return;

    const generatedAt = new Date().toLocaleString("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    });
    const amenities = selectedAmenities.length ? selectedAmenities.join(", ") : "None selected";
    const display = predictionDisplay || {};
    const carpetUnit = display.unit || prediction.carpet_area_unit || form.carpet_area_unit || "sqft";
    const detectedRateLabel = rateLabel(carpetUnit);
    const reportHtml = `
      <!doctype html>
      <html>
        <head>
          <title>PriceNest Property Report</title>
          <style>
            @page { size: A4; margin: 18mm; }
            * { box-sizing: border-box; }
            body { margin: 0; color: #102033; font-family: Arial, sans-serif; background: #ffffff; }
            .report { width: 100%; }
            .header { display: flex; align-items: center; gap: 14px; padding-bottom: 18px; border-bottom: 2px solid #123f8c; }
            .logo { width: 48px; height: 48px; display: grid; place-items: center; border-radius: 10px; background: #123f8c; color: #fff; font-weight: 800; }
            h1 { margin: 0; font-size: 28px; color: #061a3d; }
            .subtitle { margin: 4px 0 0; color: #64748b; }
            .grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 24px; }
            .item { padding: 13px; border: 1px solid #d9e2ef; border-radius: 8px; background: #f8fafd; }
            .item span { display: block; margin-bottom: 6px; color: #64748b; font-size: 12px; text-transform: uppercase; }
            .item strong { color: #061a3d; font-size: 16px; }
            .wide { grid-column: 1 / -1; }
            .footer { margin-top: 28px; padding-top: 14px; border-top: 1px solid #d9e2ef; color: #64748b; font-size: 12px; }
          </style>
        </head>
        <body>
          <main class="report">
            <section class="header">
              <div class="logo">PN</div>
              <div>
                <h1>PriceNest</h1>
                <p class="subtitle">Property Valuation Report</p>
              </div>
            </section>
            <section class="grid">
              <div class="item wide"><span>Property Details</span><strong>${prediction.property_name || "Predicted Property"}</strong></div>
              <div class="item"><span>Prediction Price</span><strong>${formatInr(display.predictedPrice || prediction.predicted_price)}</strong></div>
              <div class="item"><span>${detectedRateLabel}</span><strong>${formatRate(display.rate || prediction.price_per_sqft)}</strong></div>
              <div class="item"><span>Carpet Area</span><strong>${formatArea(display.carpetArea || prediction.carpet_area || form.carpet_area, carpetUnit)}</strong></div>
              <div class="item"><span>Total Area</span><strong>${formatArea(display.totalArea || prediction.total_area, carpetUnit)}</strong></div>
              <div class="item"><span>City</span><strong>${prediction.city || form.city}</strong></div>
              <div class="item"><span>Location</span><strong>${prediction.location || form.location}</strong></div>
              <div class="item wide"><span>Amenities</span><strong>${amenities}</strong></div>
              <div class="item wide"><span>Date & Time</span><strong>${generatedAt}</strong></div>
            </section>
            <p class="footer">Generated by PriceNest using dataset-driven Delhi NCR market insights.</p>
          </main>
          <script>window.onload = () => { window.print(); };</script>
        </body>
      </html>
    `;
    reportWindow.document.open();
    reportWindow.document.write(reportHtml);
    reportWindow.document.close();
  }

  return (
    <>
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">PN</span>
          <div>
            <strong>PriceNest</strong>
            <small>AI Real Estate Price Predictor</small>
          </div>
        </div>

        <div className="search-wrap" ref={searchDropdownRef}>
          <input
            value={query}
            placeholder="Search by location, city, property name"
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => query && setShowSuggestions(true)}
            onKeyDown={(e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    handleSearch();
  }
}}
            className={showSuggestions ? "active" : ""}
          />
          <button onClick={handleSearch} disabled={isSearching} className="search-btn">
            {isSearching ? "..." : "ðŸ”"}
          </button>
          {showSuggestions && suggestions.length > 0 && (
            <div className="autocomplete-dropdown">
              {suggestions.map((suggestion, index) => (
                <div
                  key={index}
                  className={`suggestion-item ${index === selectedSuggestionIndex ? "selected" : ""}`}
                  onClick={() => selectSuggestion(suggestion)}
                  onMouseEnter={() => setSelectedSuggestionIndex(index)}
                >
                  <div className="suggestion-main">
                    <strong>{suggestion.name}</strong>
                    <span className="suggestion-type">{suggestion.type}</span>
                  </div>
                  <small className="suggestion-city">{suggestion.city}</small>
                </div>
              ))}
            </div>
          )}
          {showSuggestions && query && suggestions.length === 0 && !isSearching && (
            <div className="autocomplete-dropdown">
              <div className="no-results">No properties found</div>
            </div>
          )}
          {showSuggestions && isSearching && (
            <div className="autocomplete-dropdown">
              <div className="loading">Searching...</div>
            </div>
          )}
        </div>

        <nav className="nav-links">
          <a href="#about">About Us</a>
          <a href="#how-it-works">How It Works</a>
          <a href="#faq">FAQs</a>
          <a href="#contact">Contact</a>
        </nav>

        <div className="account-menu-wrap">
          {currentUser ? (
            <>
              <button
                className="profile-btn"
                type="button"
                onClick={() => setIsProfileOpen((open) => !open)}
                aria-expanded={isProfileOpen}
              >
                <span className="profile-avatar">PN</span>
                <span>{currentUser.name || currentUser.email || currentUser.phone || "Profile"}</span>
              </button>
              {isProfileOpen && (
                <div className="profile-dropdown">
                  <button
                    type="button"
                    onClick={() => {
                      setIsProfileOpen(false);
                      setIsProfileModalOpen(true);
                    }}
                  >
                    <span>P</span>
                    My Profile
                  </button>
                  <button type="button" onClick={logout}>
                    <span>L</span>
                    Log Out
                  </button>
                </div>
              )}
            </>
          ) : (
            <button
              className="login-btn"
              type="button"
              onClick={() => setIsAuthOpen(true)}
            >
              Login / Register
            </button>
          )}
        </div>
      </header>

      {showSearchResults && (
        <section className="search-results">
          <div className="section-head">
            <div>
              <h2>Search Results</h2>
              <p>Found {searchResults.length} {searchResults.length === 1 ? "property" : "properties"}</p>
            </div>
            <button onClick={() => setShowSearchResults(false)}>x Close</button>
          </div>
          <div className="results-grid">
            {searchResults.length > 0 ? (
              searchResults.map((item, index) => (
                <article className="result-card" key={`${item.property_name || "property"}-${index}`}>
                  <strong>{item.property_name || "Unnamed Property"}</strong>
                  <span>{item.location || "Unknown Location"}, {item.city || "Unknown City"}</span>
                  <div>
                    <b>{formatInr(item.price)}</b>
                    <small>{item.bedrooms || "N/A"} BHK · {formatArea(item.total_area, "sqft")} · {formatRate(item.rate_per_sqft)}/sqft</small>
                  </div>
                </article>
              ))
            ) : (
              <div style={{ gridColumn: "1 / -1", textAlign: "center", padding: "40px 20px", color: "var(--muted)" }}>
                <p>No properties found. Try searching with different keywords.</p>
              </div>
            )}
          </div>
        </section>
      )}

      <main>
        <section className="hero-shell">
        <section className="hero">
          <div className="hero-copy">
            <h1>PriceNest</h1>
            <p>AI-Powered Property Valuation across Delhi &amp; Delhi NCR with Real Market Insights and Data-Driven Analysis</p>
          </div>
        </section>

        <section className="workspace">
          <form className="prediction-form" onSubmit={onPredict}>
            <section className="prediction-card">
              <div className="section-head">
                <h2>Smart Property Analyzer</h2>
                <p>Fill details and run AI prediction instantly.</p>
              </div>

              <div className="form-grid">
                {propertyFields.map(([key, label, type, required]) => (
                  <label key={key} className={key === "carpet_area" ? "wide" : ""}>
                    <span>
                      {label}
                      {required ? " *" : ""}
                    </span>
                    {type === "area" ? (
                      <div className="area-field">
                        <div className="area-combobox">
                          <input
                            type="text"
                            inputMode="decimal"
                            value={form.carpet_area}
                            onChange={(e) => updateField("carpet_area", e.target.value)}
                            onFocus={async () => {
                              setIsCarpetAreaOpen(true);
                              if (form.city && form.location && availableCarpetAreaOptions.length === 0) {
                                try {
                                  const params = new URLSearchParams({ city: form.city, location: form.location });
                                  const response = await fetch(`${API_BASE}/filter-options?${params.toString()}`);
                                  const data = await response.json();
                                  setDependentOptions(data || {});
                                } catch (error) {
                                  console.error("Failed to refresh carpet area options:", error);
                                }
                              }
                            }}
                            onBlur={() => window.setTimeout(() => setIsCarpetAreaOpen(false), 120)}
                            placeholder={isFieldUnavailable(key) ? "Not Available" : "Carpet Area"}
                            disabled={isFieldUnavailable(key)}
                            autoComplete="off"
                          />
                          {isCarpetAreaOpen && carpetAreaMatches.length > 0 && (
                            <div className="field-suggestions area-suggestions">
                              {carpetAreaMatches.map((option) => (
                                <button
                                  type="button"
                                  key={`${option.value}-${option.unit}`}
                                  onMouseDown={(event) => {
                                    event.preventDefault();
                                    setForm((prev) => ({
                                      ...prev,
                                      carpet_area: option.value,
                                      carpet_area_unit: option.unit || prev.carpet_area_unit,
                                      original_carpet_area: option.value,
                                      original_carpet_area_unit: option.unit || prev.original_carpet_area_unit,
                                    }));
                                    setIsCarpetAreaOpen(false);
                                  }}
                                >
                                  {option.value}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                        <select
                          value={form.carpet_area_unit}
                          onChange={(e) => updateCarpetAreaUnit(e.target.value)}
                          disabled={isFieldUnavailable(key)}
                        >
                          <option value="">Unit</option>
                          {(options.carpet_area_units || []).map((unit) => (
                            <option key={unit} value={unit}>
                              {unit}
                            </option>
                          ))}
                        </select>
                      </div>
                    ) : type === "search" ? (
                      <div className="location-combobox">
                        <input
                          type="text"
                          value={form[key]}
                          onChange={(e) => updateField(key, e.target.value)}
                          onFocus={() => setIsLocationOpen(true)}
                          onBlur={() => window.setTimeout(() => setIsLocationOpen(false), 120)}
                          placeholder={isFieldUnavailable(key) ? "Not Available" : `Search ${label}`}
                          disabled={isFieldUnavailable(key)}
                          autoComplete="off"
                        />
                        {isLocationOpen && locationMatches.length > 0 && (
                          <div className="field-suggestions">
                            {locationMatches.map((option) => (
                              <button
                                type="button"
                                key={option}
                                onMouseDown={(event) => {
                                  event.preventDefault();
                                  updateField(key, option);
                                  setIsLocationOpen(false);
                                }}
                              >
                                {option}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    ) : type === "select" ? (
                      <select
                        value={form[key]}
                        onChange={(e) => updateField(key, e.target.value)}
                        disabled={isFieldUnavailable(key)}
                      >
                        <option value="">{isFieldUnavailable(key) ? "Not Available" : key === "property_type" ? "Select Type" : `Select ${label}`}</option>
                        {optionsForField(key).map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type={type}
                        value={form[key]}
                        onChange={(e) => updateField(key, e.target.value)}
                        placeholder={label}
                      />
                    )}
                  </label>
                ))}
              </div>
            </section>

            <section className="amenities-card">
              <div className="section-head">
                <h2>Amenities</h2>
              </div>

              <div className="amenities-grid">
                {amenityFields.map(([key, label]) => (
                  <label key={key}>
                    <span>{label}</span>
                    {["garden_park", "main_road", "pool"].includes(key) ? (
                      <input
                        type="text"
                        value={datasetAmenityValue(key)}
                        placeholder={form.city && form.location ? "Not Available" : "Select city and location"}
                        readOnly
                        disabled={!form.city || !form.location || datasetAmenityValue(key) === "Not Available"}
                      />
                    ) : (
                      <select
                        value={form[key]}
                        onChange={(e) => updateField(key, e.target.value)}
                        disabled={isFieldUnavailable(key)}
                      >
                        <option value={isFieldUnavailable(key) ? "Not Available" : ""}>{isFieldUnavailable(key) ? "Not Available" : "Select Option"}</option>
                        {optionsForField(key).map((option) => (
                          <option key={option} value={option}>
                            {option}
                          </option>
                        ))}
                      </select>
                    )}
                  </label>
                ))}
              </div>
            </section>

            <button className="primary-btn" disabled={isPredicting}>
              {isPredicting ? "Predicting..." : "Predict Price"}
            </button>
          </form>

          <aside className="result-panel">
            <div className="result-card">
              <h3>Prediction Price</h3>
              {!prediction && <p className="muted">Submit the form to get predicted value.</p>}
              {!prediction && selectedTotalArea && (
                <div className="result-values">
                  <Metric label="Carpet Area" value={formatArea(form.carpet_area, form.carpet_area_unit || "sqft")} />
                  <Metric label="Total Area" value={formatArea(selectedTotalArea, "sqft")} />
                  <Metric label="City" value={form.city} />
                  <Metric label="Location" value={form.location} />
                </div>
              )}
              {prediction?.error && <p className="error">{prediction.error}</p>}
              {prediction && !prediction.error && (
                <div className="result-values">
                  <Metric label="Property Name" value={prediction.property_name} />
                  <Metric label="Predicted Price" value={formatInr(predictionDisplay?.predictedPrice || prediction.predicted_price)} />
                  <Metric label={rateLabel(predictionDisplay?.unit || prediction.rate_unit || prediction.carpet_area_unit || form.carpet_area_unit || "sqft")} value={formatRate(predictionDisplay?.rate || prediction.price_per_sqft)} />
                  <Metric label="Carpet Area" value={formatArea(predictionDisplay?.carpetArea || prediction.carpet_area || form.carpet_area, predictionDisplay?.unit || prediction.carpet_area_unit || form.carpet_area_unit || "sqft")} />
                  <Metric label="Total Area" value={formatArea(predictionDisplay?.totalArea || prediction.total_area, predictionDisplay?.unit || "sqft")} />
                  <Metric label="City" value={prediction.city || form.city} />
                  <Metric label="Location" value={prediction.location || form.location} />
                </div>
              )}
            </div>
            <button
              className="primary-btn print-btn"
              type="button"
              onClick={printDetails}
              disabled={!prediction || prediction.error}
            >
              Print Details
            </button>
          </aside>
        </section>
        </section>

        <MapPanel locationLabel={mapLocation || "Delhi, India"} />

        <section className="database-insights">
          <div className="section-head">
            <h2>Database Insights</h2>
            <p>Live statistics from our property dataset.</p>
          </div>
          <div className="insights-grid">
            <article className="insight-card">
              <span>Total Properties</span>
              <strong>{inventory.total_properties || 0}</strong>
            </article>
            <article className="insight-card">
              <span>1 BHK</span>
              <strong>{inventory.total_1bhk || 0}</strong>
            </article>
            <article className="insight-card">
              <span>2 BHK</span>
              <strong>{inventory.total_2bhk || 0}</strong>
            </article>
            <article className="insight-card">
              <span>3 BHK</span>
              <strong>{inventory.total_3bhk || 0}</strong>
            </article>
            <article className="insight-card">
              <span>4+ BHK</span>
              <strong>{inventory.total_4bhk_plus || 0}</strong>
            </article>
            <article className="insight-card">
              <span>Cities Covered</span>
              <strong>{inventory.total_cities || 0}</strong>
            </article>
          </div>
        </section>

        <section className="property-demand">
          <div className="section-head">
            <h2>Property Demand</h2>
            <p>Top locations by property availability.</p>
          </div>
          <div className="demand-list">
            {demand.map((item) => (
              <div className="demand-item" key={item.location}>
                <span>{item.location}</span>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${item.percentage}%` }}></div>
                </div>
                <small>{item.percentage}%</small>
              </div>
            ))}
          </div>
        </section>

        <section className="our-best-picks">
          <div className="section-head">
            <h2>Our Best Picks</h2>
            <p>{loadingHome ? "Loading best picks..." : "AI-curated property recommendations."}</p>
          </div>
          <div className="picks-grid">
            {properties.map((item, index) => (
              <article className="pick-card" key={`${item.property_name || "property"}-${index}`}>
                <div className="pick-image">
                  <img src={`https://picsum.photos/300/200?random=${index}`} alt="Property" />
                </div>
                <div className="pick-details">
                  <strong>{item.property_name || "Unnamed Property"}</strong>
                  <span>{item.location || "Unknown Location"}, {item.city || "Unknown City"}</span>
                  <div>
                    <b>{formatInr(item.price ?? item.target_price)}</b>
                    <small>{item.bedrooms || "N/A"} BHK · {formatArea(item.total_area, "sqft")} · {formatRate(item.rate_per_sqft)}/sqft</small>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        <AboutUsSection />
        <HowItWorksSection />
        <FAQSection />
        <FooterSection />
      </main>

      {isAuthOpen && (
        <AuthModal
          onClose={() => setIsAuthOpen(false)}
          onUserChange={setCurrentUser}
          authConfig={authConfig}
        />
      )}
      {isProfileModalOpen && currentUser && (
        <ProfileModal
          user={currentUser}
          onClose={() => setIsProfileModalOpen(false)}
        />
      )}
    </>
  );
}

function Metric({ label, value }) {
  const displayValue = value === null || value === undefined || value === "" ? "N/A" : value;
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{displayValue}</strong>
    </div>
  );
}

function MapPanel({ locationLabel }) {
  const encodedLocation = encodeURIComponent(locationLabel || "Delhi, India");
  const embedUrl = `https://maps.google.com/maps?hl=en&q=${encodedLocation}&z=14&ie=UTF8&iwloc=B&output=embed`;
  const mapUrl = googleMapsUrl(locationLabel);
  const facilityTypes = ["Hospital", "School", "Metro Station", "Mall"];

  return (
    <div className="map-card">
      <div className="map-head">
        <h3>Google Map</h3>
        <span>{locationLabel}</span>
      </div>

      <div className="map-frame-wrap">
        <iframe
          title="Location map"
          src={embedUrl}
          loading="lazy"
          allowFullScreen
          referrerPolicy="no-referrer-when-downgrade"
        ></iframe>
        <div className="map-fallback">
          <strong>{locationLabel}</strong>
          <span>Use the link below if this browser blocks the Google Maps preview.</span>
        </div>
      </div>
      <a className="map-open-link" href={mapUrl} target="_blank" rel="noreferrer">
        View location
      </a>

      <div className="nearby-places">
        <h4>Nearby Facilities</h4>
        <div className="places-grid static-facilities">
          {facilityTypes.map((type) => (
            <div className="place-item" key={type}>
              <strong>{type}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ProfileModal({ user, onClose }) {
  const isGoogleUser = user.provider === "google";
  const isPhoneUser = user.provider === "firebase-phone" || Boolean(user.phone);
  const [fullName, setFullName] = useState(user.name || "");

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <section className="profile-modal">
        <button type="button" className="close" onClick={onClose}>
          x
        </button>

        <div className="auth-brand">
          <span className="brand-mark">PN</span>
          <strong>PriceNest</strong>
        </div>

        <div className="profile-modal-head">
          <h2>My Profile</h2>
          <p>{isGoogleUser ? "Your Google account details are already connected." : "Your phone login profile details."}</p>
        </div>

        <div className="profile-fields">
          {isGoogleUser && (
            <>
              <label>
                <span>Full Name</span>
                <input value={user.name || "Google User"} readOnly />
              </label>
              <label>
                <span>Email Address</span>
                <input value={user.email || "Email unavailable"} readOnly />
              </label>
            </>
          )}

          {isPhoneUser && !isGoogleUser && (
            <>
              <label>
                <span>Phone Number</span>
                <input value={user.phone || "Phone unavailable"} readOnly />
              </label>
              <label>
                <span>Full Name</span>
                <input
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  placeholder="Optional"
                />
              </label>
              <p className="profile-note">Mobile OTP authentication is temporarily unavailable. Please continue using Google Sign In.</p>
            </>
          )}
        </div>
      </section>
    </div>
  );
}

function AuthModal({ onClose, onUserChange, authConfig }) {
  const [step, setStep] = useState("phone");
  const [countryCode, setCountryCode] = useState("+91");
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState(["", "", "", "", "", ""]);
  const [secondsLeft, setSecondsLeft] = useState(114);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [isSendingOtp, setIsSendingOtp] = useState(false);
  const [isVerifyingOtp, setIsVerifyingOtp] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const otpRefs = useRef([]);
  const confirmationResultRef = useRef(null);
  const recaptchaVerifierRef = useRef(null);

  useEffect(() => {
    if (step !== "otp" || secondsLeft <= 0) return undefined;
    const timer = window.setInterval(() => {
      setSecondsLeft((seconds) => Math.max(0, seconds - 1));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [step, secondsLeft]);

  useEffect(() => {
    return () => {
      if (recaptchaVerifierRef.current) {
        recaptchaVerifierRef.current.clear();
        recaptchaVerifierRef.current = null;
      }
    };
  }, []);

  const timerText = `${String(Math.floor(secondsLeft / 60)).padStart(2, "0")}:${String(secondsLeft % 60).padStart(2, "0")}`;

  function updatePhone(value) {
    setPhone(value.replace(/\D/g, "").slice(0, 10));
    setError("");
    setMessage("");
  }

  function firebaseErrorMessage(firebaseError) {
    const code = firebaseError?.code || "";
    const message = firebaseError?.message || "";
    if (code.includes("billing-not-enabled") || message.includes("billing-not-enabled")) {
      return "Mobile OTP authentication is temporarily unavailable. Please continue using Google Sign In.";
    }
    if (code.includes("invalid-phone-number")) return "Please enter a valid 10-digit mobile number";
    if (code.includes("too-many-requests")) return "Too many OTP attempts. Please try again later.";
    if (code.includes("captcha-check-failed")) return "reCAPTCHA verification failed. Please try again.";
    if (code.includes("invalid-verification-code")) return "Wrong OTP. Please try again.";
    if (code.includes("code-expired")) return "OTP expired. Please request a new OTP.";
    return "Mobile OTP authentication is temporarily unavailable. Please continue using Google Sign In.";
  }

  function getFirebaseServices() {
    if (window.pricenestFirebase?.auth) {
      return Promise.resolve(window.pricenestFirebase);
    }

    return new Promise((resolve, reject) => {
      const timeout = window.setTimeout(() => {
        reject(new Error("Firebase authentication is still loading. Please try again."));
      }, 10000);
      window.addEventListener(
        "pricenest-firebase-ready",
        () => {
          window.clearTimeout(timeout);
          resolve(window.pricenestFirebase);
        },
        { once: true }
      );
    });
  }

  function resetRecaptcha() {
    if (recaptchaVerifierRef.current) {
      recaptchaVerifierRef.current.clear();
      recaptchaVerifierRef.current = null;
    }
  }

  async function getRecaptchaVerifier(firebaseServices) {
    if (recaptchaVerifierRef.current) return recaptchaVerifierRef.current;

    recaptchaVerifierRef.current = new firebaseServices.RecaptchaVerifier(
      firebaseServices.auth,
      "firebase-recaptcha-container",
      {
        size: "invisible",
      }
    );
    await recaptchaVerifierRef.current.render();
    return recaptchaVerifierRef.current;
  }

  async function sendFirebaseOtp() {
    const firebaseServices = await getFirebaseServices();
    const verifier = await getRecaptchaVerifier(firebaseServices);
    const confirmationResult = await firebaseServices.signInWithPhoneNumber(
      firebaseServices.auth,
      `${countryCode}${phone}`,
      verifier
    );
    confirmationResultRef.current = confirmationResult;
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setMessage("");

    if (phone.length < 10) {
      setError("Please enter a valid 10-digit mobile number");
      return;
    }

    setIsSendingOtp(true);
    try {
      await sendFirebaseOtp();
      setMessage("OTP sent successfully");
      setStep("otp");
      setSecondsLeft(114);
      window.setTimeout(() => otpRefs.current[0]?.focus(), 50);
    } catch (sendError) {
      resetRecaptcha();
      setError(firebaseErrorMessage(sendError));
    } finally {
      setIsSendingOtp(false);
    }
  }

  function updateOtp(index, value) {
    const digit = value.replace(/\D/g, "").slice(-1);
    setOtp((current) => {
      const next = [...current];
      next[index] = digit;
      return next;
    });
    if (digit && index < otp.length - 1) {
      otpRefs.current[index + 1]?.focus();
    }
  }

  async function verifyOtp(event) {
    event.preventDefault();
    setError("");
    if (otp.some((digit) => !digit)) {
      setError("Please enter the 6-digit OTP");
      return;
    }
    if (!confirmationResultRef.current) {
      setError("OTP session expired. Please resend OTP.");
      return;
    }

    setIsVerifyingOtp(true);
    try {
      const credential = await confirmationResultRef.current.confirm(otp.join(""));
      const user = {
        phone: credential.user?.phoneNumber || `${countryCode} ${phone}`,
        uid: credential.user?.uid,
        provider: "firebase-phone",
      };
      localStorage.setItem("pricenest_user", JSON.stringify(user));
      onUserChange(user);
      onClose();
    } catch (verifyError) {
      setError(firebaseErrorMessage(verifyError));
    } finally {
      setIsVerifyingOtp(false);
    }
  }

  function loadGoogleScript() {
    return new Promise((resolve, reject) => {
      if (window.google?.accounts?.oauth2) {
        resolve();
        return;
      }
      const existing = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
      if (existing) {
        existing.addEventListener("load", resolve, { once: true });
        existing.addEventListener("error", reject, { once: true });
        return;
      }
      const script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  async function googleSignIn() {
    setError("");
    setMessage("");
    if (!authConfig?.google_client_id) {
      setError("Google sign in is not configured. Add GOOGLE_CLIENT_ID on the backend.");
      return;
    }

    setIsGoogleLoading(true);
    try {
      await loadGoogleScript();
      const tokenClient = window.google.accounts.oauth2.initTokenClient({
        client_id: authConfig.google_client_id,
        scope: "openid email profile",
        prompt: "select_account",
        callback: async (tokenResponse) => {
          if (tokenResponse.error || !tokenResponse.access_token) {
            setError("Google sign in failed. Please try again.");
            setIsGoogleLoading(false);
            return;
          }
          try {
            const profileResponse = await fetch("https://www.googleapis.com/oauth2/v3/userinfo", {
              headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
            });
            const profile = await profileResponse.json();
            if (!profileResponse.ok) {
              throw new Error("Google profile request failed.");
            }
            const user = {
              email: profile.email,
              name: profile.name,
              provider: "google",
              token: tokenResponse.access_token,
            };
            localStorage.setItem("pricenest_user", JSON.stringify(user));
            onUserChange(user);
            onClose();
          } catch (profileError) {
            setError("Google sign in failed. Please try again.");
          } finally {
            setIsGoogleLoading(false);
          }
        },
      });
      tokenClient.requestAccessToken();
    } catch (googleError) {
      setError("Google sign in failed. Please try again.");
      setIsGoogleLoading(false);
    }
  }

  async function resendOtp() {
    setOtp(["", "", "", "", "", ""]);
    setError("");
    setMessage("");
    setIsSendingOtp(true);
    try {
      resetRecaptcha();
      await sendFirebaseOtp();
      setMessage("OTP sent successfully");
      setSecondsLeft(114);
      window.setTimeout(() => otpRefs.current[0]?.focus(), 50);
    } catch (sendError) {
      resetRecaptcha();
      setError(firebaseErrorMessage(sendError));
    } finally {
      setIsSendingOtp(false);
    }
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <form className="auth-modal premium-auth" onSubmit={step === "phone" ? submit : verifyOtp}>
        <button type="button" className="close" onClick={onClose}>
          x
        </button>
        <div className="auth-brand">
          <span className="brand-mark">PN</span>
          <strong>PriceNest</strong>
        </div>

        {step === "phone" ? (
          <>
            <h2>Sign In or Register</h2>
            <p>Enter your 10-digit mobile number to proceed.</p>

            <label>
              <span>Mobile Number</span>
              <div className="phone-field">
                <select value={countryCode} onChange={(event) => setCountryCode(event.target.value)}>
                  <option value="+91">+91</option>
                </select>
                <input
                  type="tel"
                  inputMode="numeric"
                  value={phone}
                  onChange={(event) => updatePhone(event.target.value)}
                  placeholder="10-digit mobile number"
                />
              </div>
            </label>

            {message && <p className="auth-success">{message}</p>}
            {error && <p className="auth-error">{error}</p>}

            <button className="primary-btn auth-action" type="submit" disabled={isSendingOtp}>
              {isSendingOtp ? "Sending OTP..." : "Continue"}
            </button>

            <div className="auth-divider">
              <span></span>
              Or connect with
              <span></span>
            </div>
            <button type="button" className="google-btn" onClick={googleSignIn} disabled={isGoogleLoading}>
              <span>G</span>
              {isGoogleLoading ? "Opening Google..." : "Sign in with Google"}
            </button>
          </>
        ) : (
          <>
            <h2>Verify Your Mobile Number</h2>
            <p>A One-Time Password (OTP) has been sent to your mobile.</p>
            <div className="otp-mobile">{countryCode} {phone}</div>

            <div className="otp-grid">
              {otp.map((digit, index) => (
                <input
                  key={index}
                  ref={(element) => {
                    otpRefs.current[index] = element;
                  }}
                  type="text"
                  inputMode="numeric"
                  maxLength="1"
                  value={digit}
                  onChange={(event) => updateOtp(index, event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Backspace" && !otp[index] && index > 0) {
                      otpRefs.current[index - 1]?.focus();
                    }
                  }}
                />
              ))}
            </div>

            {message && <p className="auth-success">{message}</p>}
            {error && <p className="auth-error">{error}</p>}
            <div className="otp-row">
              <strong>Time left: {timerText}</strong>
              <button type="button" disabled={secondsLeft > 0 || isSendingOtp} onClick={resendOtp}>
                {isSendingOtp ? "Sending..." : "Resend OTP"}
              </button>
            </div>

            <button className="primary-btn auth-action" type="submit" disabled={isVerifyingOtp}>
              {isVerifyingOtp ? "Verifying..." : "Log In"}
            </button>
          </>
        )}
        <div id="firebase-recaptcha-container"></div>
      </form>
    </div>
  );
}
function AboutUsSection() {
  return (
    <section id="about" className="about-us">
      <div className="section-head">
        <h2>About Us</h2>
        <p>Discover what makes PriceNest the trusted choice for property price prediction.</p>
      </div>
      <div className="about-grid">
        <article className="about-card">
          <h3>What We Do</h3>
          <p>PriceNest turns real Delhi NCR market data into clear property valuation guidance for buyers, sellers, and investors.</p>
        </article>
        <article className="about-card">
          <h3>AI Prediction</h3>
          <p>Our analyzer reviews location, area, layout, amenities, and market patterns to produce practical price estimates.</p>
        </article>
        <article className="about-card">
          <h3>Why Trust Us</h3>
          <p>Backed by real market data and advanced algorithms, PriceNest offers transparent, data-driven insights for confident property valuation.</p>
        </article>
        <article className="about-card">
          <h3>Delhi NCR Focus</h3>
          <p>Specialized in Delhi NCR's dynamic real estate market, we provide localized intelligence for the region's most sought-after properties.</p>
        </article>
      </div>
    </section>
  );
}

function HowItWorksSection() {
  return (
    <section id="how-it-works" className="how-it-works">
      <div className="section-head">
        <h2>How It Works</h2>
        <p>Simple steps to get accurate property price predictions.</p>
      </div>
      <div className="workflow">
        <div className="step">
          <div className="step-icon">1</div>
          <h3>Select Filters</h3>
          <p>Choose your property details like location, size, bedrooms, and amenities.</p>
        </div>
        <div className="arrow">→</div>
        <div className="step">
          <div className="step-icon">2</div>
          <h3>ML Analysis</h3>
          <p>The analyzer compares your inputs with the live property dataset.</p>
        </div>
        <div className="arrow">→</div>
        <div className="step">
          <div className="step-icon">3</div>
          <h3>Price Calculation</h3>
          <p>Data-driven logic calculates a realistic price signal.</p>
        </div>
        <div className="arrow">→</div>
        <div className="step">
          <div className="step-icon">4</div>
          <h3>Results + Insights</h3>
          <p>Get your prediction along with nearby facilities and market insights.</p>
        </div>
      </div>
    </section>
  );
}

function FAQSection() {
  const [openIndex, setOpenIndex] = useState(null);

  const faqs = [
    {
      question: "How does the prediction work?",
      answer: "PriceNest compares your property inputs with real Delhi NCR market data, including location, area, bedroom count, and amenities."
    },
    {
      question: "How does the search work?",
      answer: "Search by property name, location, or city to find matching properties from our dataset. Results are filtered in real-time."
    },
    {
      question: "Is the data real?",
      answer: "Yes, all predictions are based on actual Delhi NCR property data, ensuring accurate and reliable estimates."
    },
    {
      question: "How do nearby places work?",
      answer: "Using Google Maps API, we fetch live data for hospitals, schools, metro stations, malls, and parks near your selected location."
    },
    {
      question: "Which factors affect the valuation?",
      answer: "City, locality, total area, bedrooms, floor details, facing, parking, and amenities all influence the final predicted price."
    },
    {
      question: "How accurate are the predictions?",
      answer: "Accuracy varies by location and data completeness. Areas with deeper dataset coverage generally produce more stable estimates."
    }
  ];

  return (
    <section id="faq" className="faq">
      <div className="section-head">
        <h2>FAQs</h2>
        <p>Frequently asked questions about PriceNest.</p>
      </div>
      <div className="faq-list">
        {faqs.map((faq, index) => (
          <div className="faq-item" key={index}>
            <button className="faq-question" onClick={() => setOpenIndex(openIndex === index ? null : index)}>
              {faq.question}
              <span>{openIndex === index ? "-" : "+"}</span>
            </button>
            {openIndex === index && <div className="faq-answer">{faq.answer}</div>}
          </div>
        ))}
      </div>
    </section>
  );
}

function FooterSection() {
  return (
    <footer id="contact" className="footer">
      <div className="footer-content">
        <div className="footer-section">
          <h3>About</h3>
          <p>PriceNest is your AI-powered partner for accurate Delhi NCR property price predictions.</p>
        </div>
        <div className="footer-section">
          <h3>Contact Us</h3>
          <p>Email: info@pricenest.com</p>
          <a href="https://wa.me/918368293101" target="_blank" rel="noreferrer">
            WhatsApp: +91 8368293101
          </a>
        </div>
        <div className="footer-section">
          <h3>Quick Links</h3>
          <a href="#about">About Us</a>
          <a href="#how-it-works">How It Works</a>
          <a href="#faq">FAQs</a>
        </div>
        <div className="footer-section">
          <h3>Follow Us</h3>
          <div className="social-icons">
            <a href="#">Facebook</a>
            <a href="#">Twitter</a>
            <a href="#">LinkedIn</a>
          </div>
        </div>
      </div>
      <div className="footer-bottom">
        <p>&copy; 2026 PriceNest. All rights reserved.</p>
        <div>
          <a href="#">Terms of Service</a> | <a href="#">Privacy Policy</a>
        </div>
      </div>
    </footer>
  );
}

function AboutSection() {
  return (
    <section className="about">
      <div className="section-head">
        <h2>About PriceNest</h2>
        <p>Production-style AI valuation system for real estate pricing decisions.</p>
      </div>

      <div className="about-layout">
        <table>
          <tbody>
            <tr>
              <th>Platform Goal</th>
              <td>
                Provide accurate property price predictions by combining property attributes, location
                context, and machine learning.
              </td>
            </tr>
            <tr>
              <th>How It Works</th>
              <td>
                The backend loads and preprocesses CSV data, then estimates the market price and
                rate per area unit.
              </td>
            </tr>
            <tr>
              <th>Prediction Output</th>
              <td>
                Users get predicted price, rate per area unit, and total area in one workflow.
              </td>
            </tr>
          </tbody>
        </table>

        <div className="about-cards">
          <article>
            <strong>Dynamic UI</strong>
            <span>Dropdown options, supply stats, and autocomplete are all fetched from backend APIs.</span>
          </article>
          <article>
            <strong>Practical Workflow</strong>
            <span>Top-bar search, property form, and map preview make valuation intuitive.</span>
          </article>
          <article>
            <strong>Focused Scope</strong>
            <span>No buy/rent/sell or trend modules; only AI prediction and supporting insights.</span>
          </article>
        </div>
      </div>
    </section>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
