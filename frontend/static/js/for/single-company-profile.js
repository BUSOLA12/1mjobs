async function setCountryFromOnline() {
  try {
    const response = await fetch("https://ipapi.co/json/");
    const data = await response.json();
    const countryName = data.country_name;
    const countryCode = data.country_code.toLowerCase();
	console.log(`Country updated: ${countryName}`);
    return countryName;
  } catch (error) {
    console.error("Error fetching country info:", error);
  }
}

async function getCompanyDetails(empId) {
    const res = await fetch(`/api/companies/get/${empId}/`);
    if (res.ok) {
        let data = await res.json();
        console.log("Company Details data:", data);
        return data;
    } else {
        let data = await res.json();
        throw new Error(data.error);
    }
}

function showLoading(message = null) {
    document.getElementById('loadingOverlay').classList.add('active');
    if (message !== null) {
      document.getElementById('my-pop-up').textContent = message;
    }
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

async function getCountryFlag(countryName) {
  const countryCode = getCountryCode(countryName);
  return countryCode ? `https://flagcdn.com/w20/${countryCode}.png` : null;
}

const FLAG_COUNTRY_CODES = [
  "ad", "ae", "af", "ag", "ai", "al", "am", "ao", "aq", "ar", "as", "at", "au", "aw", "ax", "az",
  "ba", "bb", "bd", "be", "bf", "bg", "bh", "bi", "bj", "bl", "bm", "bn", "bo", "bq", "br", "bs",
  "bt", "bv", "bw", "by", "bz", "ca", "cc", "cd", "cf", "cg", "ch", "ci", "ck", "cl", "cm", "cn",
  "co", "cr", "cu", "cv", "cw", "cx", "cy", "cz", "de", "dj", "dk", "dm", "do", "dz", "ec", "ee",
  "eg", "eh", "er", "es", "et", "fi", "fj", "fk", "fm", "fo", "fr", "ga", "gb", "gd", "ge", "gf",
  "gg", "gh", "gi", "gl", "gm", "gn", "gp", "gq", "gr", "gs", "gt", "gu", "gw", "gy", "hk", "hm",
  "hn", "hr", "ht", "hu", "id", "ie", "il", "im", "in", "io", "iq", "ir", "is", "it", "je", "jm",
  "jo", "jp", "ke", "kg", "kh", "ki", "km", "kn", "kp", "kr", "kw", "ky", "kz", "la", "lb", "lc",
  "li", "lk", "lr", "ls", "lt", "lu", "lv", "ly", "ma", "mc", "md", "me", "mf", "mg", "mh", "mk",
  "ml", "mm", "mn", "mo", "mp", "mq", "mr", "ms", "mt", "mu", "mv", "mw", "mx", "my", "mz", "na",
  "nc", "ne", "nf", "ng", "ni", "nl", "no", "np", "nr", "nu", "nz", "om", "pa", "pe", "pf", "pg",
  "ph", "pk", "pl", "pm", "pn", "pr", "ps", "pt", "pw", "py", "qa", "re", "ro", "rs", "ru", "rw",
  "sa", "sb", "sc", "sd", "se", "sg", "sh", "si", "sj", "sk", "sl", "sm", "sn", "so", "sr", "ss",
  "st", "sv", "sx", "sy", "sz", "tc", "td", "tf", "tg", "th", "tj", "tk", "tl", "tm", "tn", "to",
  "tr", "tt", "tv", "tw", "tz", "ua", "ug", "um", "us", "uy", "uz", "va", "vc", "ve", "vg", "vi",
  "vn", "vu", "wf", "ws", "xk", "ye", "yt", "za", "zm", "zw"
];

const COUNTRY_CODE_ALIASES = {
  "america": "us", "britain": "gb", "burma": "mm", "cape verde": "cv",
  "congo brazzaville": "cg", "congo kinshasa": "cd", "cote d ivoire": "ci",
  "czech republic": "cz", "czechia": "cz", "democratic republic of the congo": "cd",
  "dr congo": "cd", "england": "gb", "great britain": "gb", "ivory coast": "ci",
  "macedonia": "mk", "north korea": "kp", "north macedonia": "mk",
  "palestine": "ps", "republic of korea": "kr", "republic of the congo": "cg",
  "russia": "ru", "scotland": "gb", "south korea": "kr", "swaziland": "sz",
  "syria": "sy", "tanzania": "tz", "uae": "ae", "uk": "gb",
  "united kingdom": "gb", "united states": "us", "united states of america": "us",
  "us": "us", "usa": "us", "vietnam": "vn", "viet nam": "vn", "wales": "gb"
};

let regionDisplayNames = null;

function normalizeCountryName(countryName) {
  return String(countryName || "")
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase()
    .replace(/&/g, " and ").replace(/[^a-z0-9]+/g, " ").trim();
}

function getRegionDisplayNames() {
  if (regionDisplayNames !== null) return regionDisplayNames;
  regionDisplayNames = typeof Intl !== "undefined" && Intl.DisplayNames
    ? new Intl.DisplayNames(["en"], { type: "region" }) : false;
  return regionDisplayNames;
}

function getCountryCode(countryName) {
  const normalizedCountryName = normalizeCountryName(countryName);
  if (!normalizedCountryName) return null;
  if (/^[a-z]{2}$/.test(normalizedCountryName) && FLAG_COUNTRY_CODES.includes(normalizedCountryName)) {
    return normalizedCountryName;
  }
  if (COUNTRY_CODE_ALIASES[normalizedCountryName]) {
    return COUNTRY_CODE_ALIASES[normalizedCountryName];
  }
  const displayNames = getRegionDisplayNames();
  if (!displayNames) return null;
  return FLAG_COUNTRY_CODES.find((countryCode) => {
    try {
      return normalizeCountryName(displayNames.of(countryCode.toUpperCase())) === normalizedCountryName;
    } catch (error) {
      return false;
    }
  }) || null;
}

function setCountryFlag(flagUrl, countryName) {
  const flagImg = document.getElementById("country-flag");
  const placeholder = document.getElementById("country-flag-placeholder");
  if (!flagImg || !placeholder) return;
  if (flagUrl) {
    flagImg.onerror = () => {
      flagImg.onerror = null;
      setCountryFlag(null, countryName);
    };
    flagImg.src = flagUrl;
    flagImg.alt = `${countryName} flag`;
    flagImg.style.display = "inline-block";
    placeholder.style.display = "none";
  } else {
    flagImg.onerror = null;
    flagImg.removeAttribute("src");
    flagImg.alt = "";
    flagImg.style.display = "none";
    placeholder.style.display = countryName ? "inline-block" : "none";
  }
}

function setCompanyLogo(logoUrl) {
  const logoImg = document.getElementById("company-logo");
  const placeholder = document.getElementById("company-logo-placeholder");
  if (!logoImg || !placeholder) return;
  if (logoUrl) {
    logoImg.src = logoUrl;
    logoImg.style.display = "block";
    placeholder.style.display = "none";
  } else {
    logoImg.removeAttribute("src");
    logoImg.style.display = "none";
    placeholder.style.display = "flex";
  }
}

let jobLocationMap = null;
let jobLocationMarker = null;
let jobLocationPanorama = null;
let googleMapsAuthFailed = false;

function normalizeLocationPart(value) {
  return String(value || "").trim();
}

function buildJobLocationAddress(company) {
  const parts = [company.headquarters_address, company.company_country]
    .map(normalizeLocationPart)
    .filter(Boolean);
  return parts
    .filter((part, index) => {
      const normalizedPart = part.toLowerCase();
      return parts.findIndex((candidate) => candidate.toLowerCase() === normalizedPart) === index;
    })
    .join(", ");
}

function showLocationSnackbar(message) {
  if (window.Snackbar) {
    Snackbar.show({ text: message, pos: "bottom-center", showAction: true, actionText: "Dismiss", duration: 3000, textColor: "#fff", backgroundColor: "#fa0404ff" });
    return;
  }
  console.warn(message);
}

function setStreetViewButtonState(enabled) {
  const streetViewButton = document.getElementById("streetView");
  if (!streetViewButton) return;
  streetViewButton.setAttribute("aria-disabled", enabled ? "false" : "true");
}

function googleMapsAvailable() {
  if (googleMapsAuthFailed) return false;
  return Boolean(window.google && google.maps && google.maps.Map && google.maps.Geocoder && google.maps.StreetViewService);
}

function geocodeJobAddress(address) {
  return new Promise((resolve, reject) => {
    const geocoder = new google.maps.Geocoder();
    geocoder.geocode({ address }, (results, status) => {
      if (status === "OK" && results && results[0]) {
        resolve(results[0]);
        return;
      }
      reject(new Error("Could not find this location on Google Maps."));
    });
  });
}

function bindUnavailableStreetView(message) {
  const streetViewButton = document.getElementById("streetView");
  if (!streetViewButton) return;
  setStreetViewButtonState(false);
  streetViewButton.onclick = (event) => {
    event.preventDefault();
    showLocationSnackbar(message);
  };
}

async function initCompanyLocationMap(company) {
  const mapElement = document.getElementById("singleListingMap");
  const streetViewButton = document.getElementById("streetView");
  const address = buildJobLocationAddress(company);

  if (!mapElement || !streetViewButton) return;
  if (!address) {
    bindUnavailableStreetView("Location is not available.");
    return;
  }
  if (googleMapsAuthFailed) {
    bindUnavailableStreetView("Google Maps API key is not authorized for this site URL.");
    return;
  }
  if (!googleMapsAvailable()) {
    bindUnavailableStreetView("Google Maps is not available right now.");
    return;
  }

  try {
    const geocodeResult = await geocodeJobAddress(address);
    const position = geocodeResult.geometry.location;

    mapElement.dataset.latitude = position.lat();
    mapElement.dataset.longitude = position.lng();

    jobLocationMap = new google.maps.Map(mapElement, {
      zoom: 15, center: position, scrollwheel: false,
      streetViewControl: true, mapTypeControl: false,
      fullscreenControl: true, gestureHandling: "cooperative",
    });
    jobLocationMarker = new google.maps.Marker({
      position, map: jobLocationMap, title: address,
    });
    jobLocationPanorama = jobLocationMap.getStreetView();
    const streetViewService = new google.maps.StreetViewService();
    setStreetViewButtonState(true);
    streetViewButton.onclick = (event) => {
      event.preventDefault();
      streetViewService.getPanorama(
        { location: position, radius: 1000, source: google.maps.StreetViewSource.OUTDOOR },
        (panoramaData, status) => {
          if (status === "OK" && panoramaData && panoramaData.location && panoramaData.location.latLng) {
            jobLocationPanorama.setPosition(panoramaData.location.latLng);
            jobLocationPanorama.setPov({ heading: 0, pitch: 0 });
            jobLocationPanorama.setVisible(true);
            return;
          }
          showLocationSnackbar("Street View is not available for this location.");
        }
      );
    };
  } catch (error) {
    console.error(error);
    bindUnavailableStreetView(error.message);
  }
}

window.addEventListener("google-maps-auth-failure", () => {
  googleMapsAuthFailed = true;
  bindUnavailableStreetView("Google Maps API key is not authorized for this site URL.");
});

document.addEventListener("DOMContentLoaded", async function () {
    const companyId = window.location.pathname.split("/").filter(Boolean).pop();
    showLoading();
    updateUserNavInfo();

    try {
        const comp_data = await getCompanyDetails(companyId);
        console.log("Company data:", comp_data);
        
        setCompanyLogo(comp_data.logo_url);

        document.querySelector("#country-name").textContent = comp_data.company_country || ""; 
        document.querySelector("#company-name").textContent = comp_data.company_name; 
        document.querySelector("h3").textContent = comp_data.company_name;

        const flagUrl = await getCountryFlag(comp_data.company_country);
        setCountryFlag(flagUrl, comp_data.company_country);

        document.querySelector("#summary-location").textContent = comp_data.headquarters_address || comp_data.company_country || "Not specified";
        
        const indMap = {
            'information_technology': 'Information Technology',
            'accounting_and_finance': 'Accounting and Finance',
            // Can add more industry mapping if needed, fallback to raw value
        };
        const industry = comp_data.industry || "";
        document.querySelector("#summary-industry").textContent = indMap[industry] || industry.replace(/_/g, ' ') || "Not specified";

document.querySelector("#company-description").textContent = comp_data.description || "No description available.";
        initCompanyLocationMap(comp_data);
        
        // Show verified badge only if company is verified
        const verifiedBadge = document.querySelector(".verified-badge-with-title");
        if (comp_data.verified) {
            verifiedBadge.style.display = "block";
        } else {
            verifiedBadge.style.display = "none";
        }
        
        hideLoading();
    } catch (error) {
        Snackbar.show({
            text: `Company could not be loaded: ${error.message}`,
            pos: "bottom-center", showAction: true, actionText: "Dismiss",
            duration: 3000, textColor: "#fff", backgroundColor: "#fc0707ff",
        });
        hideLoading();
        console.error(error);
    }
});
