require 'yaml'
require 'fileutils'

class ConfigManager
  # Saves config in ~/.config/sacct_api/config.yml (macOS/Linux standard)
  CONFIG_DIR = File.expand_path('~/config')
  CONFIG_FILE = File.join(CONFIG_DIR, 'config.yml')

  # Default values if no file exists yet
  DEFAULT_CONFIG = {
    'url' => 'https://127.0.0.1:5000',
    'ssl' => false
  }.freeze

  def self.load
    return DEFAULT_CONFIG.dup unless File.exist?(CONFIG_FILE)

    YAML.load_file(CONFIG_FILE) || DEFAULT_CONFIG.dup
  rescue StandardError => e
    puts "Warning: Failed to load config (#{e.message}). Using defaults."
    DEFAULT_CONFIG.dup
  end

  def self.save(url:, ssl:)
    FileUtils.mkdir_p(CONFIG_DIR) unless Dir.exist?(CONFIG_DIR)

    config = {
      'url' => url,
      'ssl' => ssl
    }

    File.write(CONFIG_FILE, YAML.dump(config))
    puts "Saved settings to #{CONFIG_FILE}"
  end
end