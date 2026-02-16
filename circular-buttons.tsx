
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Edit,
  Plus,
  Minus,
  Check,
  X,
  Heart,
  Star,
  Share,
  Download,
  Upload,
  Settings,
  User,
  Bell,
  MessageCircle,
  Phone,
  Mail,
  Camera,
  Search,
  Filter,
  MoreHorizontal,
  ChevronRight,
  ChevronLeft,
  Play,
  Pause,
  Volume2,
  Bookmark,
} from "lucide-react"

export default function CircularButtons() {
  return (
    <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Circular Button Variations</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Small Circular Buttons */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Small Circular Buttons (24px)</h3>
            <div className="flex flex-wrap gap-2">
              <Button className="w-6 h-6 bg-teal-600 hover:bg-teal-700 rounded-full p-0 border-0">
                <Plus className="w-3 h-3 text-white" />
              </Button>
              <Button className="w-6 h-6 bg-red-500 hover:bg-red-600 rounded-full p-0 border-0">
                <Minus className="w-3 h-3 text-white" />
              </Button>
              <Button className="w-6 h-6 bg-green-500 hover:bg-green-600 rounded-full p-0 border-0">
                <Check className="w-3 h-3 text-white" />
              </Button>
              <Button className="w-6 h-6 bg-gray-500 hover:bg-gray-600 rounded-full p-0 border-0">
                <X className="w-3 h-3 text-white" />
              </Button>
              <Button className="w-6 h-6 bg-pink-500 hover:bg-pink-600 rounded-full p-0 border-0">
                <Heart className="w-3 h-3 text-white" />
              </Button>
            </div>
          </div>

          {/* Medium Circular Buttons */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Medium Circular Buttons (32px)</h3>
            <div className="flex flex-wrap gap-3">
              <Button className="w-8 h-8 bg-blue-600 hover:bg-blue-700 rounded-full p-0 border-0">
                <Edit className="w-4 h-4 text-white" />
              </Button>
              <Button className="w-8 h-8 bg-purple-600 hover:bg-purple-700 rounded-full p-0 border-0">
                <Star className="w-4 h-4 text-white" />
              </Button>
              <Button className="w-8 h-8 bg-orange-600 hover:bg-orange-700 rounded-full p-0 border-0">
                <Share className="w-4 h-4 text-white" />
              </Button>
              <Button className="w-8 h-8 bg-indigo-600 hover:bg-indigo-700 rounded-full p-0 border-0">
                <Download className="w-4 h-4 text-white" />
              </Button>
              <Button className="w-8 h-8 bg-emerald-600 hover:bg-emerald-700 rounded-full p-0 border-0">
                <Upload className="w-4 h-4 text-white" />
              </Button>
            </div>
          </div>

          {/* Large Circular Buttons */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Large Circular Buttons (48px)</h3>
            <div className="flex flex-wrap gap-4">
              <Button className="w-12 h-12 bg-teal-600 hover:bg-teal-700 rounded-full p-0 border-0">
                <Settings className="w-6 h-6 text-white" />
              </Button>
              <Button className="w-12 h-12 bg-slate-600 hover:bg-slate-700 rounded-full p-0 border-0">
                <User className="w-6 h-6 text-white" />
              </Button>
              <Button className="w-12 h-12 bg-amber-600 hover:bg-amber-700 rounded-full p-0 border-0">
                <Bell className="w-6 h-6 text-white" />
              </Button>
              <Button className="w-12 h-12 bg-cyan-600 hover:bg-cyan-700 rounded-full p-0 border-0">
                <MessageCircle className="w-6 h-6 text-white" />
              </Button>
            </div>
          </div>

          {/* Extra Large Circular Buttons */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Extra Large Circular Buttons (64px)</h3>
            <div className="flex flex-wrap gap-4">
              <Button className="w-16 h-16 bg-green-600 hover:bg-green-700 rounded-full p-0 border-0">
                <Phone className="w-8 h-8 text-white" />
              </Button>
              <Button className="w-16 h-16 bg-red-600 hover:bg-red-700 rounded-full p-0 border-0">
                <Mail className="w-8 h-8 text-white" />
              </Button>
              <Button className="w-16 h-16 bg-violet-600 hover:bg-violet-700 rounded-full p-0 border-0">
                <Camera className="w-8 h-8 text-white" />
              </Button>
            </div>
          </div>

          {/* Outlined Circular Buttons */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Outlined Circular Buttons</h3>
            <div className="flex flex-wrap gap-3">
              <Button className="w-10 h-10 bg-transparent hover:bg-teal-50 rounded-full p-0 border-2 border-teal-600">
                <Search className="w-5 h-5 text-teal-600" />
              </Button>
              <Button className="w-10 h-10 bg-transparent hover:bg-blue-50 rounded-full p-0 border-2 border-blue-600">
                <Filter className="w-5 h-5 text-blue-600" />
              </Button>
              <Button className="w-10 h-10 bg-transparent hover:bg-gray-50 rounded-full p-0 border-2 border-gray-600">
                <MoreHorizontal className="w-5 h-5 text-gray-600" />
              </Button>
            </div>
          </div>

          {/* Navigation Circular Buttons */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Navigation Circular Buttons</h3>
            <div className="flex flex-wrap gap-3">
              <Button className="w-10 h-10 bg-gray-200 hover:bg-gray-300 rounded-full p-0 border-0">
                <ChevronLeft className="w-5 h-5 text-gray-700" />
              </Button>
              <Button className="w-10 h-10 bg-gray-200 hover:bg-gray-300 rounded-full p-0 border-0">
                <ChevronRight className="w-5 h-5 text-gray-700" />
              </Button>
              <Button className="w-12 h-12 bg-green-600 hover:bg-green-700 rounded-full p-0 border-0">
                <Play className="w-6 h-6 text-white ml-1" />
              </Button>
              <Button className="w-12 h-12 bg-red-600 hover:bg-red-700 rounded-full p-0 border-0">
                <Pause className="w-6 h-6 text-white" />
              </Button>
            </div>
          </div>

          {/* Floating Action Buttons */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Floating Action Buttons</h3>
            <div className="flex flex-wrap gap-4">
              <Button className="w-14 h-14 bg-teal-600 hover:bg-teal-700 rounded-full p-0 border-0 shadow-lg hover:shadow-xl transition-shadow">
                <Plus className="w-7 h-7 text-white" />
              </Button>
              <Button className="w-12 h-12 bg-blue-600 hover:bg-blue-700 rounded-full p-0 border-0 shadow-lg hover:shadow-xl transition-shadow">
                <Volume2 className="w-6 h-6 text-white" />
              </Button>
              <Button className="w-12 h-12 bg-purple-600 hover:bg-purple-700 rounded-full p-0 border-0 shadow-lg hover:shadow-xl transition-shadow">
                <Bookmark className="w-6 h-6 text-white" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
