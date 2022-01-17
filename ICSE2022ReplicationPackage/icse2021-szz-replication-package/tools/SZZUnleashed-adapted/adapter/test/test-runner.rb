require 'minitest/autorun'
require 'tmpdir'
require 'json'

require_relative '../src/szz-runner'

describe SZZUnleashed do
    project_dir = File.dirname(File.expand_path(File.join(__FILE__, "../..")))
    szz_dir     = File.join(project_dir, "szz")
    szz_jar     = File.join(szz_dir, "build/libs/szz_find_bug_introducers-0.1.jar")
    
    it "should correctly build the target jar" do
        File.unlink(szz_jar) if FileTest.exist? szz_jar
        
        result = SZZUnleashed.build
        
        assert_equal true, result
        assert_equal true, FileTest.exist?(szz_jar)
    end
    
    it "should create a gitlog.json file just outside the repo folder" do
        Dir.mktmpdir do |dir|
            SZZUnleashed.generate_git_log('https://github.com/octocat/Hello-World', dir + "/test-repo")
            
            assert_equal true, FileTest.exist?(File.join(dir, 'gitlog.json'))
        end
    end
    
    it "should create a correct JSON array with the issues" do
        c1 = FixCommit.new
        c1.hash      = "02d6908ada70fcf8012833ddef628bc09c6f8389"
        c1.issue_url = "https://bugs.launchpad.net/cinder/+bug/1046985"
        
        c2 = FixCommit.new
        c2.hash      = "ddef628bc09c6f838902d6908ada70fcf8012833"
        c2.issue_url = "https://bugs.launchpad.net/kicad/+bug/1771003"
        
        fix_commits = [c1, c2]
        
        Dir.mktmpdir do |dir|
            output_file = File.join(dir, "issues.json")
            
            SZZUnleashed.generate_issue_file(fix_commits, output_file)
            assert_equal true, FileTest.exist?(output_file)
            
            json = JSON.parse(File.read(output_file))
            assert_equal 2, json.size
            
            assert_equal(true, json.values.all? { |e| e['hash'].is_a?(String) })
            assert_equal(true, json.values.all? { |e| e['creationdate'].is_a?(String) })
            assert_equal(true, json.values.all? { |e| e['commitdate'] == nil })
            assert_equal(true, json.values.all? { |e| e['resolutiondate'] == nil })
            assert_equal "02d6908ada70fcf8012833ddef628bc09c6f8389", json.values[0]['hash']
        end
    end
end
