// Shared country-flag helper.
// Maps a country name (e.g. "Nigeria") or ISO code (e.g. "ng") to a flagcdn URL
// that works for every country, unlike the local /static/images/flags set which
// only holds a handful of SVGs. Exposes a synchronous window.getFlagUrl(name).
(function () {
  if (window.getFlagUrl) return; // already provided

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
    "america": "us",
    "britain": "gb",
    "burma": "mm",
    "cape verde": "cv",
    "congo brazzaville": "cg",
    "congo kinshasa": "cd",
    "cote d ivoire": "ci",
    "czech republic": "cz",
    "czechia": "cz",
    "democratic republic of the congo": "cd",
    "dr congo": "cd",
    "england": "gb",
    "great britain": "gb",
    "ivory coast": "ci",
    "macedonia": "mk",
    "north korea": "kp",
    "north macedonia": "mk",
    "palestine": "ps",
    "republic of korea": "kr",
    "republic of the congo": "cg",
    "russia": "ru",
    "scotland": "gb",
    "south korea": "kr",
    "swaziland": "sz",
    "syria": "sy",
    "tanzania": "tz",
    "uae": "ae",
    "uk": "gb",
    "united kingdom": "gb",
    "united states": "us",
    "united states of america": "us",
    "us": "us",
    "usa": "us",
    "vietnam": "vn",
    "viet nam": "vn",
    "wales": "gb"
  };

  let regionDisplayNames = null;

  function normalizeCountryName(countryName) {
    return String(countryName || "")
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toLowerCase()
      .replace(/&/g, " and ")
      .replace(/[^a-z0-9]+/g, " ")
      .trim();
  }

  function getRegionDisplayNames() {
    if (regionDisplayNames !== null) return regionDisplayNames;
    regionDisplayNames = typeof Intl !== "undefined" && Intl.DisplayNames
      ? new Intl.DisplayNames(["en"], { type: "region" })
      : false;
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

  // Synchronous: returns a flag image URL for a country name/code, or null.
  function getFlagUrl(countryName) {
    const code = getCountryCode(countryName);
    return code ? `https://flagcdn.com/w40/${code}.png` : null;
  }

  window.getFlagUrl = getFlagUrl;
})();
