package org.heli;

import java.awt.Color;
import java.awt.Frame;
import java.awt.Graphics;
import java.awt.MenuContainer;
import java.awt.Transparency;
import java.awt.color.ColorSpace;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;
import java.awt.image.BufferedImage;
import java.awt.image.ColorModel;
import java.awt.image.ComponentColorModel;
import java.awt.image.DataBuffer;
import java.awt.image.DataBufferByte;
import java.awt.image.Raster;
import java.awt.image.WritableRaster;
import java.io.BufferedInputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.HashMap;
import java.util.Hashtable;

import javax.imageio.ImageIO;
import javax.swing.Action;
import javax.swing.BorderFactory;
import javax.swing.BoxLayout;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JPanel;

import com.jogamp.opengl.GL;
import com.jogamp.opengl.GL2;
import com.jogamp.opengl.GLAutoDrawable;
import com.jogamp.opengl.GLEventListener;
import com.jogamp.opengl.awt.GLCanvas;
import com.jogamp.opengl.util.texture.Texture;
import com.jogamp.opengl.util.texture.TextureData;
import com.jogamp.opengl.util.texture.TextureIO;

public class MainWindow extends JFrame implements ActionListener, ItemListener {

	private JMenuBar menuBar;
	private JMenu fileMenu;
	private JMenuItem fmenuQuit;
	//JMenu displayMenu;
	private World theWorld;
	private long lastDisplayedTime;

	private int myWidth;
	private int myHeight;
    public Heli_GL_Panel m_glPanel = null;

    public MainWindow(World world, String windowTitle, int w, int h, GLCanvas canvas)
	{
		super(windowTitle);
        theWorld = world;
        System.out.println("*********** World: " + world + ", the: " + theWorld);
		JPanel base = new JPanel();
		add(base);
		base.setLayout(new BoxLayout(base, BoxLayout.LINE_AXIS));
		base.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));
		m_glPanel = new Heli_GL_Panel(this,world,h,w);
		m_glPanel.setLayout(new BoxLayout(m_glPanel,BoxLayout.PAGE_AXIS));
		base.add(m_glPanel);
		theWorld.m_chopperInfoPanel = new JPanel();
		theWorld.m_chopperInfoPanel.setLayout(new BoxLayout(theWorld.m_chopperInfoPanel,BoxLayout.PAGE_AXIS));
		theWorld.m_chopperInfoPanel.setBorder(BorderFactory.createEmptyBorder(0,10,10,10));
		base.add(theWorld.m_chopperInfoPanel);
		myWidth = m_glPanel.getWidth();
		myHeight = m_glPanel.getHeight();
		m_glPanel.add(canvas);
		setVisible(true);
		setFocusable(true);
        setSize(w,h);
		
		lastDisplayedTime = System.nanoTime();
		this.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		/*addWindowListener(new WindowAdapter() {
			public void windowClosing(WindowEvent e) {
				System.exit(0);
			}
		}); */
		menuBar = new JMenuBar();
		fileMenu = new JMenu("File");
		//displayMenu = new JMenu("Display");
		fileMenu.setMnemonic(KeyEvent.VK_F);
		menuBar.add(fileMenu);
		//menuBar.add(displayMenu);
		
		fmenuQuit = new JMenuItem("Quit", KeyEvent.VK_Q);
		fileMenu.add(fmenuQuit);
		fmenuQuit.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent event) {
				System.exit(0);
			}
		});
		setJMenuBar(menuBar);
		theWorld.addPanels();
	}

    @Override
	public void itemStateChanged(ItemEvent arg0) {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void actionPerformed(ActionEvent e) {
		// TODO Auto-generated method stub
		
	}
	
	public void render(GLAutoDrawable drawable)
	{
        long currentTime = System.nanoTime();
        long deltaTime = currentTime - lastDisplayedTime;
        if (deltaTime > 1000000000)
        {
            this.setTitle("Elapsed Time: " + (Math.round(theWorld.getTimestamp() * 1000.0) / 1000.0) + " s");
            lastDisplayedTime = currentTime;
        }
	    
	}
}
