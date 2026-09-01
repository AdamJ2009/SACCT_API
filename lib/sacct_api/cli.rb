# frozen_string_literal: true

require 'bundler/setup'
require 'date'
require 'dry/cli'
require 'fileutils'
require 'json'
require 'yaml'

require_relative 'version'
require_relative 'renderer'
require_relative '../config/configmanager'

module SacctApi
  module CLI
    # CLI commands
    module Commands
      extend Dry::CLI::Registry

      # Update the config file for url changes
      module Config
        # Sets config values
        class Set < Dry::CLI::Command
          desc 'Save API configuration settings'
          option :url, aliases: ['-u'], type: :string, desc: 'API base URL'
          option :ssl, alaises: ['-s'], type: :boolean, desc: 'Verify SSL certificate'

          def call(**opts)
            current = ConfigManager.load
            new_url = opts[:url] || current['url']
            new_ssl = opts.key?(:ssl) ? opts[:ssl] : current['ssl']

            ConfigManager.save(url: new_url, ssl: new_ssl)
          end
        end

        # Shows current values
        class Show < Dry::CLI::Command
          desc 'Display current API configuration settings'

          def call(**)
            config = ConfigManager.load
            puts "Config File: #{ConfigManager::CONFIG_FILE}"
            puts "URL:         #{config['url']}"
            puts "SSL Verify:  #{config['ssl']}"
          end
        end
      end

      # Reports back the json file
      class Report < Dry::CLI::Command
        desc 'Report based on flags sent to the cli'
        option :days, aliases: ['-d', '--date'], type: :integer, desc: 'Go back n amount of days'
        option :timespread, aliases: ['-t', '--times'], type: :boolean, desc: 'Show 7,30,90 days'
        option :user, aliases: ['-u', '--username'], type: :string, desc: 'Select user(leave blank for self)'
        option :json, aliases: ['-j'], type: :string, desc: 'Save json if not none'

        def call(**opts)
          result = api_call(opts)
          return if result.nil? # If no results, do not render anything

          # This invokes SacctApi::Renderer.new(result).render
          Renderer.render(result)

          return if opts[:json].nil? # If not requesting json

          # Json printout
          json = json_check!(opts[:json])
          File.write(json, JSON.pretty_generate(result))
        end

        private

        def api_call(opts)
          user = opts[:user].nil? ? current_user : opts[:user]
          days = opts[:days].nil? ? 30 : opts[:days]
          opts[:timespread] ? timespread(user) : single_time(user, days)
        end

        def current_user
          Etc.getlogin || ENV['USER'] || ENV['LOGNAME'] || Etc.getpwuid(Process.uid)&.name
        rescue StandardError
          ENV['USER']
        end

        def timespread(user)
          cmd = "curl #{url}/user/#{user}"
          raw_response = `#{cmd}`
          JSON.parse(raw_response, symbolize_names: true)
        end

        def single_time(user, days)
          cmd = "curl #{url}/user/#{user}/#{days}"
          raw_response = `#{cmd}`
          JSON.parse(raw_response, symbolize_names: true)
        end

        def url
          config = ConfigManager.load
          url = config['url']
          ssl = config['ssl'] ? '' : '-k '
          ssl + url
        end

        def json_check!(filename)
          unless filename =~ /\.json$/i
            puts "Error: Invalid json filename '#{filename}'. Must end with .json"
            exit 1
          end
          filename
        end
      end

      # Gives version
      class Version < Dry::CLI::Command
        desc 'Print the version'

        def call(*)
          puts "SacctAPI version #{SacctApi::VERSION}"
        end
      end
      register 'config set', Config::Set
      register 'config show', Config::Show
      register 'report', Report
      register 'version', Version, aliases: ['-v', '--version']
    end
  end
end
