# frozen_string_literal: true

require 'tty-table'

module SacctApi

  # TTY table renderer
  class Renderer
    def self.render(_data)
      quota_table(_data)
    end
    private
    def quota_table(data)
      # Extract the filesystem path and data
      fs_path, fs_info = data[:quota_filesystem].first

      # Build dynamic header and values from the JSON structure
      headers = ['Filesystem', 'Used Bytes', 'Quota Bytes', 'Limit Bytes', 'Used Files', 'Quota Files', 'Limit Files']
      row = [
        fs_path.to_s,
        fs_info.dig(:blocks, :used_bytes),
        fs_info.dig(:blocks, :quota_bytes),
        fs_info.dig(:blocks, :limit_bytes),
        fs_info.dig(:files, :used),
        fs_info.dig(:files, :quota),
        fs_info.dig(:files, :limit)
      ]

      table = TTY::Table.new(
        header: headers,
        rows: [row]
      )

      puts table.render(:ascii)
    end
  end
end
