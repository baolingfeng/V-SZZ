require 'minitest/autorun'
require_relative '../src/issue-trackers'
 
describe Launchpad do
    it "should parse the correct creation date" do
        url = "https://bugs.launchpad.net/cinder/+bug/1046985"
        
        issue = IssueTracker.handler_for(url).fetch(url)
        
        assert_equal 1346957157, issue.creation_date.to_i
    end
end

describe Jira do
    it "should parse the correct creation date" do
        url = "https://jira.percona.com/browse/FB8-212"
        
        issue = IssueTracker.handler_for(url).fetch(url)
        
        assert_equal 1547157272, issue.creation_date.to_i
    end
end

describe Bugzilla do
    it "should parse the correct creation date for https://bugzilla.redhat.com/show_bug.cgi?id=1113474" do
        url = "https://bugzilla.redhat.com/show_bug.cgi?id=1113474"
        
        issue = IssueTracker.handler_for(url).fetch(url)
        
        assert_equal 1403774280, issue.creation_date.to_i
    end
    
    it "should parse the correct creation date for https://bugzilla.gnome.org/show_bug.cgi?id=753181" do
        url = "https://bugzilla.gnome.org/show_bug.cgi?id=753181"
        
        issue = IssueTracker.handler_for(url).fetch(url)
        
        assert_equal 1438610040, issue.creation_date.to_i
    end
    
    it "should parse the correct creation date for https://bugzilla.tianocore.org/show_bug.cgi?id=2365" do
        url = "https://bugzilla.tianocore.org/show_bug.cgi?id=2365"
        
        issue = IssueTracker.handler_for(url).fetch(url)
        
        assert_equal 1574235300, issue.creation_date.to_i
    end
end

describe GitHub do
    it "should parse the correct creation date" do
        url = "https://github.com/analogdevicesinc/linux/issues/143"
        
        issue = IssueTracker.handler_for(url).fetch(url)
        
        assert_equal 1530799461, issue.creation_date.to_i
    end
end

describe GitLab do
    it "should parse the correct creation date" do
        url = "https://gitlab.gnome.org/GNOME/gtk/issues/1316"
        
        issue = IssueTracker.handler_for(url).fetch(url)
        
        assert_equal 1536192389, issue.creation_date.to_i
    end
end

describe SourceForge do
    it "should parse the correct creation date" do
        url = "https://sourceforge.net/p/net-snmp/bugs/2294/"
        
        issue = IssueTracker.handler_for(url).fetch(url)
        
        assert_equal 1317940680, issue.creation_date.to_i
    end
end

describe Trac do
    it "should parse the correct creation date" do
        url = "https://trac.sagemath.org/ticket/25494"
        
        issue = IssueTracker.handler_for(url).fetch(url)
        
        assert_equal 1527885067, issue.creation_date.to_i
    end
end

describe Redmine do
    it "should parse the correct creation date" do
        url = "https://projects.theforeman.org/issues/24709"
        
        issue = IssueTracker.handler_for(url).fetch(url)
        
        assert_equal 1535096820, issue.creation_date.to_i
    end
end

describe MantisBT do
    it "should parse the correct creation date" do
        url = "https://tracker.freecadweb.org/view.php?id=1740"
        
        issue = IssueTracker.handler_for(url).fetch(url)
        
        assert_equal 1410382620, issue.creation_date.to_i
    end
end

describe NoIssueTracker do
    it "should return an empty issue when a null url is passed" do
        issue = IssueTracker.handler_for(nil).fetch(nil)
        
        assert_nil issue.creation_date
        assert_nil issue.url
    end
end
