# frozen_string_literal: true

require 'tty-table'
require_relative 'error_handler'

module SacctApi
  # TTY table renderer
  class Renderer
    EFFICIENCY_HEADERS = ['Job count', 'Queue Time(avg)', 'Run time(Avg)', 'CPU eff', 'Mem Eff'].freeze
    SHAPE_HEADERS = ['Type', 'Count', 'Avg CPU', 'Avg Node', 'Avg CPU/Node'].freeze
    QUOTA_HEADERS = ['Filesystem', 'Used Bytes', 'Quota Bytes', 'Limit Bytes', 'Used Files', 'Quota Files',
                     'Limit Files'].freeze

    def initialize(data)
      @data = data
    end

    def self.render(data)
      new(data).render
    end

    def render
      value = check_if_json_ok
      value.positive? ? ErrorHandler.print(value, @data) : render_values
    end

    private

    def render_values
      if @data.key?(:days_back)
        puts efficiency_table
        puts "\n"
        puts job_table
        puts "\n"
      end

      return unless @data.key?(:quota_filesystem)

      puts 'Usage Quota table'
      puts quota_table
    end

    def check_if_json_ok
      return 1 if @data.nil?
      return 2 if @data.key?(:Error)
      return 3 if @data.dig(:last, :submit) =~ /^Not within \d+ days$/

      0
    end

    def title(table, multiple)
      if multiple
        puts "#{table} table over range"
      else
        days = @data[:days_back].keys.first
        puts "#{table} table for #{days} days"
      end
    end

    def table_render(headers, rows, multiline: false, style: :unicode)
      return '' if rows.empty?

      table = TTY::Table.new(header: headers, rows: rows)
      border_opts = multiline ? { separator: :each_row } : {}

      table.render(style, multiline: multiline, border: border_opts, padding: [0, 1, 0, 0])
    end

    def efficiency_table
      multiple = @data[:days_back].size > 1
      title('Efficency', multiple)

      headers = multiple ? ['Days'] + EFFICIENCY_HEADERS : EFFICIENCY_HEADERS
      rows = @data[:days_back].map do |fs_path, fs_info|
        row = [
          fs_info.dig(:jobs, :count),
          fs_info.dig(:jobs, :average_queue),
          fs_info.dig(:jobs, :average_time),
          fs_info.dig(:efficiency, :"cpu%"),
          fs_info.dig(:efficiency, :"mem%")
        ]
        multiple ? [fs_path.to_s] + row : row
      end

      table_render(headers, rows)
    end

    def job_table
      multiple = @data[:days_back].size > 1
      title('Job Shape', multiple)

      if multiple
        headers = ['Days back', 'Job Shapes Summary']
        rows = @data[:days_back].map { |path, info| [path.to_s, job_table_individual(info, false)] }
        table_render(headers, rows, multiline: true, style: :unicode)
      else
        fs_info = @data[:days_back].values.first
        job_table_individual(fs_info, true)
      end
    end

    def job_table_individual(passed_data, single)
      shapes = passed_data.dig(:jobs, :shapes)
      return '-' if shapes.nil? || shapes.empty?

      rows = shapes.map do |fs_path, fs_info|
        [
          fs_path.to_s,
          fs_info[:count],
          fs_info.fetch(:avg_cpu, '-'),
          fs_info.fetch(:avg_node, '-'),
          fs_info.fetch(:avg_cpu_per_node, '-')
        ]
      end

      style = single ? :unicode : :basic
      table_render(SHAPE_HEADERS, rows, style: style)
    end

    def quota_table
      rows = @data[:quota_filesystem].map do |fs_path, fs_info|
        [
          fs_path.to_s,
          fs_info.dig(:blocks, :used_bytes),
          fs_info.dig(:blocks, :quota_bytes),
          fs_info.dig(:blocks, :limit_bytes),
          fs_info.dig(:files, :used),
          fs_info.dig(:files, :quota),
          fs_info.dig(:files, :limit)
        ]
      end

      table_render(QUOTA_HEADERS, rows)
    end
  end
end
